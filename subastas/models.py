from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from usuarios.models import CustomUser

class Categoria(models.Model):
    nombre = models.CharField(max_length=50, blank=False, unique=True)

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.nombre

class Subasta(models.Model):
    ESTADO_CHOICES = (
        ('abierta', 'Abierta'),
        ('cerrada', 'Cerrada'),
    )
    
    titulo = models.CharField(max_length=150)
    descripcion = models.TextField()
    precio_inicial = models.DecimalField(
        max_digits=10, 
        decimal_places=2,
        validators=[MinValueValidator(0.01, message="El precio debe ser mayor que 0")]
    )
    valoracion = models.DecimalField(
        max_digits=3, 
        decimal_places=2,
        validators=[
            MinValueValidator(1.0, message="La valoración debe ser al menos 1.0"),
            MaxValueValidator(5.0, message="La valoración no puede ser mayor a 5.0")
        ]
    )
    stock = models.IntegerField(
        validators=[MinValueValidator(1, message="El stock debe ser al menos 1")]
    )
    marca = models.CharField(max_length=100)
    categoria = models.ForeignKey(
        Categoria, related_name="subastas", on_delete=models.CASCADE
    )
    imagen = models.URLField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_cierre = models.DateTimeField()
    estado = models.CharField(
        max_length=10,
        choices=ESTADO_CHOICES,
        default='abierta'
    )
    
    # Relación con el usuario que crea la subasta
    usuario = models.ForeignKey(
        CustomUser, 
        related_name="subastas", 
        on_delete=models.CASCADE,
        null=True  # Temporalmente permitimos valores nulos para migración
    )

    class Meta:
        ordering = ("id",)

    def __str__(self):
        return self.titulo
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validar que la fecha de cierre sea posterior a la fecha de creación
        if self.fecha_cierre and self.fecha_cierre <= timezone.now():
            raise ValidationError({
                'fecha_cierre': 'La fecha de cierre debe ser posterior a la fecha actual'
            })
        
        # Validar que la fecha de cierre sea al menos 15 días después de la fecha actual
        min_fecha_cierre = timezone.now() + timedelta(days=15)
        if self.fecha_cierre and self.fecha_cierre < min_fecha_cierre:
            raise ValidationError({
                'fecha_cierre': 'La fecha de cierre debe ser al menos 15 días después de la fecha actual'
            })
    
    def save(self, *args, **kwargs):
        # Actualizar el estado de la subasta según la fecha de cierre
        if self.fecha_cierre and self.fecha_cierre <= timezone.now():
            self.estado = 'cerrada'
        else:
            self.estado = 'abierta'
        
        self.full_clean()  # Ejecutar validaciones antes de guardar
        super().save(*args, **kwargs)

class Puja(models.Model):
    subasta = models.ForeignKey(
        Subasta, related_name="pujas", on_delete=models.CASCADE
    )
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)
    fecha_puja = models.DateTimeField(auto_now_add=True)
    
    # Cambiando el campo pujador de CharField a ForeignKey
    pujador = models.ForeignKey(
        CustomUser,
        related_name="pujas",
        on_delete=models.CASCADE,
        null=True  # Temporalmente permitimos valores nulos para migración
    )

    class Meta:
        ordering = ("-fecha_puja",)  # Ordenar por fecha de puja descendente

    def __str__(self):
        # Actualizar para manejar pujador como objeto CustomUser
        return f"{self.pujador.username} - ${self.cantidad} - {self.subasta.titulo}"
