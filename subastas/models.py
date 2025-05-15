from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from usuarios.models import CustomUser
from django.db.models import Avg

class Categoria(models.Model):
    """
    Modelo que representa las categorías de productos para las subastas.
    
    Cada subasta pertenece a una categoría específica (por ejemplo: Smartphones, Laptops, Belleza).
    Las categorías permiten agrupar y filtrar subastas por tipo de producto.
    """
    nombre = models.CharField(max_length=50, unique=True)

    class Meta:
        ordering = ("id",)  # Ordenar las categorías por ID de forma ascendente

    def __str__(self):
        """Representación en texto del objeto categoría."""
        return self.nombre

class Subasta(models.Model):
    """
    Modelo principal que representa una subasta de producto.
    
    Este modelo contiene toda la información relevante sobre un producto en subasta:
    características, precio inicial, estado, propietario, etc. 
    Las subastas pueden estar en estado 'abierta' o 'cerrada' según su fecha de cierre.
    """
    # Opciones predefinidas para el campo estado
    ESTADO_CHOICES = (('abierta', 'Abierta'), ('cerrada', 'Cerrada'))
    
    titulo = models.CharField(max_length=150)  # Título descriptivo de la subasta
    descripcion = models.TextField()  # Descripción detallada del producto
    precio_inicial = models.DecimalField(max_digits=10, decimal_places=2, validators=[MinValueValidator(0.01)])  # Precio mínimo para comenzar las pujas
    valoracion = models.DecimalField(max_digits=3, decimal_places=2, validators=[MinValueValidator(1.0), MaxValueValidator(5.0)], default=1.0)  # Valoración media del producto (1-5)
    stock = models.IntegerField(validators=[MinValueValidator(1)])  # Cantidad disponible del producto
    marca = models.CharField(max_length=100)  # Marca del producto
    categoria = models.ForeignKey(Categoria, related_name="subastas", on_delete=models.CASCADE)  # Categoría a la que pertenece
    imagen = models.URLField()  # URL de la imagen del producto
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Fecha automática de creación
    fecha_cierre = models.DateTimeField()  # Fecha en que finaliza la subasta
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='abierta')  # Estado actual de la subasta
    usuario = models.ForeignKey(CustomUser, related_name="subastas", on_delete=models.CASCADE, null=True)  # Usuario que creó la subasta

    class Meta:
        ordering = ("id",)  # Ordenar las subastas por ID de forma ascendente

    def __str__(self):
        """Representación en texto del objeto subasta."""
        return self.titulo
    
    def save(self, *args, **kwargs):
        """
        Sobrescribe el método save para actualizar automáticamente el estado
        de la subasta según su fecha de cierre al guardar.
        """
        if self.fecha_cierre and self.fecha_cierre <= timezone.now():
            self.estado = 'cerrada'  # Si la fecha de cierre ha pasado, cambia a 'cerrada'
        else:
            self.estado = 'abierta'  # Si no, mantiene estado 'abierta'
        super().save(*args, **kwargs)

    def get_valoracion_media(self):
        """
        Calcula y devuelve la valoración media de la subasta basada en los ratings.
        Si no hay ratings, devuelve la valoración actual o 1.0 como valor por defecto.
        """
        try:
            ratings = Rating.objects.filter(subasta=self)  # Obtiene todos los ratings de esta subasta
            if ratings.exists():
                # Calcula el promedio y redondea a 2 decimales
                return round(ratings.aggregate(avg_valor=Avg('valor'))['avg_valor'], 2)
            return self.valoracion or 1.0  # Si no hay ratings, usa el valor actual o 1.0
        except:
            return self.valoracion or 1.0  # En caso de error, devuelve el valor actual o 1.0

class Puja(models.Model):
    """
    Modelo que representa una puja (oferta) realizada por un usuario en una subasta.
    
    Cada puja está asociada a una subasta específica y registra la cantidad ofertada,
    el usuario que la realizó y la fecha en que se hizo.
    """
    subasta = models.ForeignKey(Subasta, related_name="pujas", on_delete=models.CASCADE)  # Subasta asociada a esta puja
    cantidad = models.DecimalField(max_digits=10, decimal_places=2)  # Monto ofertado
    fecha_puja = models.DateTimeField(auto_now_add=True)  # Fecha y hora automática de la puja
    pujador = models.ForeignKey(CustomUser, related_name="pujas", on_delete=models.CASCADE, null=True)  # Usuario que realizó la puja

    class Meta:
        ordering = ("-fecha_puja",)  # Ordenar pujas por fecha de manera descendente (más recientes primero)

    def __str__(self):
        """Representación en texto del objeto puja."""
        return f"{self.pujador.username} - ${self.cantidad} - {self.subasta.titulo}"

class Rating(models.Model):
    """
    Modelo que representa una valoración realizada por un usuario a una subasta.
    
    Cada valoración tiene un valor numérico (1-5) y está asociada a un usuario
    y una subasta específica. Un usuario solo puede valorar una vez cada subasta.
    """
    valor = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)])  # Valoración numérica (1-5)
    usuario = models.ForeignKey(CustomUser, related_name="ratings", on_delete=models.CASCADE)  # Usuario que hizo la valoración
    subasta = models.ForeignKey(Subasta, related_name="ratings", on_delete=models.CASCADE)  # Subasta valorada
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Fecha y hora de creación
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Fecha y hora de última actualización

    class Meta:
        unique_together = ('usuario', 'subasta')  # Un usuario solo puede valorar una vez cada subasta
        ordering = ('-fecha_actualizacion',)  # Ordenar por fecha de actualización descendente
        db_table = 'subastas_rating'  # Nombre explícito de la tabla en la base de datos

    def __str__(self):
        """Representación en texto del objeto rating."""
        return f"{self.usuario.username} valoró {self.subasta.titulo} con {self.valor}"

class Comentario(models.Model):
    """
    Modelo que representa un comentario realizado por un usuario en una subasta.
    
    Los comentarios permiten a los usuarios expresar opiniones o hacer preguntas
    sobre los productos en subasta. Cada comentario tiene un título, un texto,
    y está asociado a un usuario y una subasta específica.
    """
    titulo = models.CharField(max_length=100)  # Título breve del comentario
    texto = models.TextField()  # Contenido principal del comentario
    fecha_creacion = models.DateTimeField(auto_now_add=True)  # Fecha y hora de creación
    fecha_actualizacion = models.DateTimeField(auto_now=True)  # Fecha y hora de última actualización
    usuario = models.ForeignKey(CustomUser, related_name="comentarios", on_delete=models.CASCADE)  # Usuario que hizo el comentario
    subasta = models.ForeignKey(Subasta, related_name="comentarios", on_delete=models.CASCADE)  # Subasta comentada

    class Meta:
        ordering = ('-fecha_creacion',)  # Ordenar por fecha de creación descendente (más recientes primero)
        verbose_name = "Comentario"
        verbose_name_plural = "Comentarios"

    def __str__(self):
        """Representación en texto del objeto comentario."""
        return f"{self.usuario.username}: {self.titulo} - {self.subasta.titulo}"
