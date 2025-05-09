from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from datetime import timedelta
from usuarios.models import CustomUser
from django.db.models import Avg

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
        ],
        default=1.0  # Ahora el valor por defecto es 1.0
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

    def get_valoracion_media(self):
        """
        Calcula la valoración media de la subasta basada en los ratings de los usuarios.
        Si no hay valoraciones o hay algún error, devuelve el valor actual de valoracion o 1.0
        """
        try:
            # Intentar obtener las valoraciones
            ratings = Rating.objects.filter(subasta=self)
            
            if ratings.exists():
                # Calcular la media si hay valoraciones
                valoracion_media = ratings.aggregate(avg_valor=Avg('valor'))['avg_valor']
                # Redondear a 2 decimales para que sea compatible con el campo en Subasta
                valoracion_media = round(valoracion_media, 2)
                
                # Actualizar el campo valoracion en la subasta para mantener compatibilidad
                if self.valoracion != valoracion_media:
                    Subasta.objects.filter(id=self.id).update(valoracion=valoracion_media)
                    
                return valoracion_media
            
            # Si no hay valoraciones, devolver el valor actual o 1.0
            return self.valoracion if hasattr(self, 'valoracion') and self.valoracion else 1.0
        except Exception as e:
            # Si hay cualquier error (por ejemplo, problemas con la base de datos),
            # simplemente devolver el valor actual de valoracion
            return self.valoracion if hasattr(self, 'valoracion') and self.valoracion else 1.0

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

class Rating(models.Model):
    """Modelo para las valoraciones de usuarios a las subastas"""
    valor = models.IntegerField(
        validators=[
            MinValueValidator(1, message="La valoración mínima es 1"),
            MaxValueValidator(5, message="La valoración máxima es 5")
        ]
    )
    usuario = models.ForeignKey(
        CustomUser,
        related_name="ratings",
        on_delete=models.CASCADE
    )
    subasta = models.ForeignKey(
        Subasta,
        related_name="ratings",
        on_delete=models.CASCADE
    )
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)

    class Meta:
        # Cada usuario solo puede valorar una vez cada subasta
        unique_together = ('usuario', 'subasta')
        ordering = ('-fecha_actualizacion',)
        # Añadir esta opción para usar la tabla existente sin intentar recrearla
        db_table = 'subastas_rating'

    def __str__(self):
        return f"{self.usuario.username} valoró {self.subasta.titulo} con {self.valor}"

class Comentario(models.Model):
    """Modelo para los comentarios de las subastas"""
    titulo = models.CharField(max_length=100)
    texto = models.TextField()
    fecha_creacion = models.DateTimeField(auto_now_add=True)
    fecha_actualizacion = models.DateTimeField(auto_now=True)
    usuario = models.ForeignKey(
        CustomUser,
        related_name="comentarios",
        on_delete=models.CASCADE
    )
    subasta = models.ForeignKey(
        Subasta,
        related_name="comentarios",
        on_delete=models.CASCADE
    )

    class Meta:
        ordering = ('-fecha_creacion',)
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"

    def __str__(self):
        return f"{self.usuario.username}: {self.titulo} - {self.subasta.titulo}"
