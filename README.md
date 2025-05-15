# PacomprarServer - API de Subastas

## Descripción

PacomprarServer es un sistema de backend para una plataforma de subastas online. Proporciona una API RESTful completa que permite a los usuarios crear y participar en subastas, realizar pujas, valorar productos y hacer comentarios.

## Tecnologías utilizadas

- **Framework**: Django 5.2 / Django REST Framework
- **Base de datos**: SQLite (desarrollo local) / PostgreSQL (producción)
- **Autenticación**: JWT (JSON Web Tokens) con SimpleJWT
- **Documentación API**: drf-spectacular (OpenAPI/Swagger)

## Configuración de entorno de desarrollo

### Requisitos previos

- Python 3.10+
- Pip (gestor de paquetes de Python)

### Instalación

1. Clonar el repositorio:
   ```bash
   git clone <URL_del_repositorio>
   cd Pacomprar_backend/PacomprarServer
   ```

2. Instalar dependencias:
   ```bash
   pip install -r requirements.txt
   ```

3. Configurar la base de datos (SQLite para desarrollo local):
   ```bash
   python manage.py migrate
   ```

4. Cargar datos de prueba:
   ```bash
   python populate_db.py
   ```

5. Iniciar el servidor de desarrollo:
   ```bash
   python manage.py runserver
   ```

El servidor estará disponible en `http://127.0.0.1:8000/`.

## Arquitectura del sistema

El proyecto sigue una arquitectura REST basada en Django REST Framework, donde cada recurso se expone a través de endpoints específicos que siguen el patrón MVC (Modelo-Vista-Controlador):

1. **Modelos**: Definen la estructura de datos y la lógica de negocio
2. **Serializadores**: Convierten objetos Python a JSON y viceversa, además de validar datos
3. **Vistas**: Procesan las solicitudes HTTP y devuelven respuestas, implementando la lógica de la API
4. **URLs**: Definen las rutas que conectan las solicitudes HTTP con las vistas correspondientes

### Flujo de procesamiento de una petición:

1. La solicitud HTTP llega a una URL definida
2. La URL enruta la solicitud a la vista apropiada
3. La vista utiliza serializadores para validar y procesar los datos
4. Los serializadores interactúan con los modelos para leer o escribir en la base de datos
5. La vista devuelve una respuesta con datos serializados

## Análisis detallado de la API

A continuación, analizamos cada endpoint, mostrando cómo se interconectan los modelos, serializadores y vistas.

### Autenticación

#### `/api/token/` (POST)

**Descripción**: Obtiene tokens JWT para autenticación

**Implementación**:
- **Vista**: `CustomTokenObtainPairView` en `usuarios/views.py`
- **Serializador**: `CustomTokenObtainPairSerializer` que extiende `TokenObtainPairSerializer`
- **Modelo**: Utiliza `CustomUser` para validar credenciales
- **Funcionamiento**: El serializador valida las credenciales del usuario contra la base de datos y genera un par de tokens JWT (acceso y refresco)

#### `/api/token/refresh/` (POST)

**Descripción**: Refresca un token JWT de acceso utilizando el token de refresco

**Implementación**:
- **Vista**: `TokenRefreshView` de `rest_framework_simplejwt`
- **Funcionamiento**: Verifica que el token de refresco sea válido y genera un nuevo token de acceso

#### `/api/usuarios/register/` (POST)

**Descripción**: Registra un nuevo usuario en el sistema

**Implementación**:
- **Vista**: `UserRegisterView` en `usuarios/views.py`
- **Serializador**: `UserSerializer` en `usuarios/serializers.py`
- **Modelo**: `CustomUser` en `usuarios/models.py`
- **Funcionamiento**: 
  1. El serializador valida los datos del usuario (incluyendo contraseñas coincidentes)
  2. Crea un nuevo usuario en la base de datos
  3. Genera tokens JWT para la sesión inicial
  4. Devuelve los datos del usuario y los tokens

#### `/api/usuarios/log-out/` (POST)

**Descripción**: Cierra la sesión invalidando el token JWT

**Implementación**:
- **Vista**: `LogoutView` en `usuarios/views.py`
- **Funcionamiento**: 
  1. Recibe el token de refresco en la solicitud
  2. Lo añade a la lista negra de tokens
  3. Esto invalida tanto el token de refresco como el de acceso asociado

### Gestión de usuarios

#### `/api/usuarios/` (GET)

**Descripción**: Lista todos los usuarios registrados (solo administradores)

**Implementación**:
- **Vista**: `UserListView` en `usuarios/views.py`
- **Serializador**: `UserSerializer` en `usuarios/serializers.py`
- **Modelo**: `CustomUser` en `usuarios/models.py`
- **Permisos**: `IsAdminUser` (solo administradores pueden acceder)
- **Funcionamiento**: Consulta todos los usuarios en la base de datos y los serializa para su presentación

#### `/api/usuarios/<id>/` (GET, PUT, DELETE)

**Descripción**: Gestiona un usuario específico (solo administradores)

**Implementación**:
- **Vista**: `UserRetrieveUpdateDestroyView` en `usuarios/views.py`
- **Serializador**: `UserSerializer` en `usuarios/serializers.py`
- **Modelo**: `CustomUser` en `usuarios/models.py`
- **Permisos**: `IsAdminUser` (solo administradores pueden acceder)
- **Funcionamiento**:
  - **GET**: Obtiene los datos del usuario y los serializa
  - **PUT**: Actualiza los datos del usuario, validando con el serializador
  - **DELETE**: Elimina al usuario de la base de datos

#### `/api/usuarios/profile/` (GET, PATCH, DELETE)

**Descripción**: Permite a un usuario autenticado gestionar su propio perfil

**Implementación**:
- **Vista**: `UserProfileView` en `usuarios/views.py`
- **Serializador**: `UserSerializer` en `usuarios/serializers.py`
- **Modelo**: `CustomUser` en `usuarios/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**:
  - **GET**: Obtiene los datos del usuario actual y los serializa
  - **PATCH**: Actualiza parcialmente los datos del usuario, validando con el serializador
  - **DELETE**: Elimina la cuenta del usuario actual

#### `/api/usuarios/change-password/` (POST)

**Descripción**: Cambia la contraseña del usuario autenticado

**Implementación**:
- **Vista**: `ChangePasswordView` en `usuarios/views.py`
- **Serializador**: `ChangePasswordSerializer` en `usuarios/serializers.py`
- **Modelo**: `CustomUser` en `usuarios/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**:
  1. Valida la contraseña actual
  2. Valida que la nueva contraseña cumpla con las políticas de seguridad
  3. Actualiza la contraseña en la base de datos

### Gestión de subastas

#### `/api/subastas/` (GET, POST)

**Descripción**: Lista todas las subastas o crea una nueva

**Implementación**:
- **Vista**: `SubastaListCreate` en `subastas/views.py`
- **Serializador**: `SubastaSerializer` en `subastas/serializers.py`
- **Modelo**: `Subasta` en `subastas/models.py`
- **Permisos**: `IsAuthenticatedOrReadOnly` (cualquiera puede ver, solo autenticados pueden crear)
- **Funcionamiento**:
  - **GET**: 
    1. Consulta todas las subastas, filtrando por estado o categoría si se especifica
    2. Serializa los resultados, incluyendo información calculada como precio actual
  - **POST**: 
    1. Valida los datos de entrada (fecha de cierre, precio inicial, etc.)
    2. Crea una nueva subasta asociada al usuario autenticado

#### `/api/subastas/<id_subasta>/` (GET, PUT, DELETE)

**Descripción**: Gestiona una subasta específica

**Implementación**:
- **Vista**: `SubastaRetrieveUpdateDestroy` en `subastas/views.py`
- **Serializador**: `SubastaDetailSerializer` en `subastas/serializers.py`
- **Modelo**: `Subasta` en `subastas/models.py`
- **Permisos**: `IsOwnerOrAdmin` (solo el creador o administradores)
- **Funcionamiento**:
  - **GET**: 
    1. Obtiene la subasta específica
    2. Serializa los resultados, incluyendo información detallada como pujas, valoraciones y comentarios asociados
  - **PUT/PATCH**: 
    1. Valida los datos de actualización
    2. Actualiza la subasta si el usuario es propietario o administrador
  - **DELETE**: 
    1. Elimina la subasta y todos sus elementos asociados (pujas, valoraciones, comentarios)

#### `/api/misSubastas/` (GET)

**Descripción**: Lista todas las subastas creadas por el usuario autenticado

**Implementación**:
- **Vista**: `UserSubastaListView` en `subastas/views.py`
- **Serializador**: `SubastaSerializer` en `subastas/serializers.py`
- **Modelo**: `Subasta` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**:
  1. Filtra las subastas donde el usuario es el creador
  2. Serializa los resultados para devolverlos en la respuesta

### Gestión de categorías

#### `/api/subastas/categorias/` (GET, POST)

**Descripción**: Lista todas las categorías o crea una nueva

**Implementación**:
- **Vista**: `CategoriaListCreate` en `subastas/views.py`
- **Serializador**: `CategoriaSerializer` en `subastas/serializers.py`
- **Modelo**: `Categoria` en `subastas/models.py`
- **Permisos**: `IsAdminOrReadOnly` (cualquiera puede ver, solo administradores pueden crear)
- **Funcionamiento**:
  - **GET**: Obtiene todas las categorías sin paginación
  - **POST**: Solo administradores pueden crear nuevas categorías

#### `/api/subastas/categoria/<id_categoria>/` (GET)

**Descripción**: Obtiene detalles de una categoría específica

**Implementación**:
- **Vista**: `CategoriaRetrieve` en `subastas/views.py`
- **Serializador**: `CategoriaSerializer` en `subastas/serializers.py`
- **Modelo**: `Categoria` en `subastas/models.py`
- **Permisos**: `IsAdminOrReadOnly` (cualquiera puede ver)
- **Funcionamiento**: Obtiene y serializa los datos de una categoría específica

#### `/api/subasta/categoria/<id_categoria>/` (PUT, DELETE)

**Descripción**: Actualiza o elimina una categoría específica

**Implementación**:
- **Vista**: `CategoriaUpdateDestroy` en `subastas/views.py`
- **Serializador**: `CategoriaSerializer` en `subastas/serializers.py`
- **Modelo**: `Categoria` en `subastas/models.py`
- **Permisos**: `IsAdminOrReadOnly` (solo administradores pueden modificar o eliminar)
- **Funcionamiento**:
  - **PUT**: Actualiza los datos de la categoría
  - **DELETE**: Elimina la categoría (solo si no tiene subastas asociadas para evitar inconsistencias)

### Gestión de pujas

#### `/api/subastas/<id_subasta>/pujas/` (GET, POST)

**Descripción**: Lista todas las pujas de una subasta o crea una nueva

**Implementación**:
- **Vista**: `PujaListCreate` en `subastas/views.py`
- **Serializador**: `PujaSerializer` en `subastas/serializers.py`
- **Modelo**: `Puja` en `subastas/models.py`
- **Permisos**: `IsAuthenticatedOrReadOnly` (cualquiera puede ver, solo autenticados pueden pujar)
- **Funcionamiento**:
  - **GET**: 
    1. Obtiene todas las pujas para la subasta especificada, ordenadas por cantidad descendente
    2. Actualiza el estado de la subasta a "cerrada" si ha pasado su fecha de cierre
  - **POST**: 
    1. Verifica que la subasta esté abierta
    2. Valida que la cantidad sea mayor que la puja más alta o que el precio inicial
    3. Asocia la puja al usuario autenticado y a la subasta especificada

#### `/api/subastas/<id_subasta>/pujas/<idPuja>/` (GET, PUT, DELETE)

**Descripción**: Gestiona una puja específica

**Implementación**:
- **Vista**: `PujaRetrieveUpdateDestroy` en `subastas/views.py`
- **Serializador**: `PujaDetailSerializer` en `subastas/serializers.py`
- **Modelo**: `Puja` en `subastas/models.py`
- **Permisos**: `IsPujaOwnerOrAdmin` (solo el autor de la puja o administradores)
- **Funcionamiento**:
  - **GET**: Obtiene y serializa los detalles de la puja
  - **PUT**: 
    1. Verifica que la subasta esté abierta
    2. Actualiza la puja si el usuario es propietario o administrador
  - **DELETE**:
    1. Verifica que la subasta esté abierta
    2. Elimina la puja si el usuario es propietario o administrador

#### `/api/misPujas/` (GET)

**Descripción**: Lista todas las pujas realizadas por el usuario autenticado

**Implementación**:
- **Vista**: `UserPujaListView` en `subastas/views.py`
- **Serializador**: `PujaSerializer` en `subastas/serializers.py`
- **Modelo**: `Puja` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**: Filtra y devuelve todas las pujas donde el usuario autenticado es el pujador

### Gestión de valoraciones (ratings)

#### `/api/subastas/<id_subasta>/ratings/` (GET, POST)

**Descripción**: Lista todas las valoraciones de una subasta o crea una nueva

**Implementación**:
- **Vista**: `RatingListCreate` en `subastas/views.py`
- **Serializador**: `RatingSerializer` en `subastas/serializers.py`
- **Modelo**: `Rating` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**:
  - **GET**: Obtiene todas las valoraciones para la subasta especificada
  - **POST**: 
    1. Verifica que el usuario no haya valorado antes esta subasta
    2. Crea la valoración asociada al usuario y la subasta
    3. Recalcula y actualiza la valoración media de la subasta

#### `/api/subastas/<id_subasta>/ratings/<id_rating>/` (GET, PUT, DELETE)

**Descripción**: Gestiona una valoración específica

**Implementación**:
- **Vista**: `RatingDetailView` en `subastas/views.py`
- **Serializador**: `RatingSerializer` en `subastas/serializers.py`
- **Modelo**: `Rating` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (el usuario debe estar autenticado)
- **Funcionamiento**:
  - **GET**: Obtiene y serializa los detalles de la valoración
  - **PUT**: 
    1. Actualiza la valoración
    2. Recalcula y actualiza la valoración media de la subasta
  - **DELETE**:
    1. Verifica que el usuario sea propietario o administrador
    2. Elimina la valoración
    3. Recalcula y actualiza la valoración media de la subasta

#### `/api/subastas/<id_subasta>/mi-rating/` (GET, DELETE)

**Descripción**: Gestiona la valoración del usuario autenticado para una subasta específica

**Implementación**:
- **Vista**: `UserRatingView` en `subastas/views.py`
- **Serializador**: `RatingSerializer` en `subastas/serializers.py`
- **Modelo**: `Rating` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**:
  - **GET**: Obtiene la valoración del usuario para esta subasta (404 si no existe)
  - **DELETE**: 
    1. Elimina la valoración del usuario para esta subasta
    2. Recalcula y actualiza la valoración media de la subasta

#### `/api/misValoraciones/` (GET)

**Descripción**: Lista todas las valoraciones realizadas por el usuario autenticado

**Implementación**:
- **Vista**: `UserRatingListView` en `subastas/views.py`
- **Serializador**: `RatingSerializer` en `subastas/serializers.py`
- **Modelo**: `Rating` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**: Filtra y devuelve todas las valoraciones donde el usuario autenticado es el autor

### Gestión de comentarios

#### `/api/subastas/<id_subasta>/comentarios/` (GET, POST)

**Descripción**: Lista todos los comentarios de una subasta o crea uno nuevo

**Implementación**:
- **Vista**: `ComentarioListCreate` en `subastas/views.py`
- **Serializador**: `ComentarioSerializer` en `subastas/serializers.py`
- **Modelo**: `Comentario` en `subastas/models.py`
- **Permisos**: `IsAuthenticatedOrReadOnly` (cualquiera puede ver, solo autenticados pueden comentar)
- **Funcionamiento**:
  - **GET**: Obtiene todos los comentarios para la subasta especificada
  - **POST**: Crea un nuevo comentario asociado al usuario autenticado y a la subasta

#### `/api/subastas/<id_subasta>/comentarios/<id_comentario>/` (GET, PUT, DELETE)

**Descripción**: Gestiona un comentario específico

**Implementación**:
- **Vista**: `ComentarioDetailView` en `subastas/views.py`
- **Serializador**: `ComentarioSerializer` en `subastas/serializers.py`
- **Modelo**: `Comentario` en `subastas/models.py`
- **Permisos**: `IsComentarioOwnerOrAdmin` (solo el autor del comentario o administradores)
- **Funcionamiento**:
  - **GET**: Obtiene y serializa los detalles del comentario
  - **PUT**: Actualiza el comentario si el usuario es propietario o administrador
  - **DELETE**: Elimina el comentario si el usuario es propietario o administrador

#### `/api/misComentarios/` (GET)

**Descripción**: Lista todos los comentarios realizados por el usuario autenticado

**Implementación**:
- **Vista**: `UserComentarioListView` en `subastas/views.py`
- **Serializador**: `ComentarioSerializer` en `subastas/serializers.py`
- **Modelo**: `Comentario` en `subastas/models.py`
- **Permisos**: `IsAuthenticated` (solo usuarios autenticados)
- **Funcionamiento**: Filtra y devuelve todos los comentarios donde el usuario autenticado es el autor

## Clases de permisos personalizados

El sistema implementa permisos personalizados para controlar el acceso a los recursos. A continuación se detallan los permisos y su funcionamiento:

### `IsOwnerOrAdmin` (`permissions.py`)

**Descripción**: Permite acceso completo a administradores y propietarios del objeto, solo lectura para otros.

**Implementación**:
```python
def has_object_permission(self, request, view, obj):
    # Permitir GET, HEAD, OPTIONS a cualquier usuario
    if request.method in permissions.SAFE_METHODS:
        return True
    
    # Administradores tienen acceso completo
    if request.user.is_staff:
        return True
    
    # El propietario del objeto tiene acceso completo
    return obj.usuario == request.user
```

**Uso**: Aplicado principalmente en vistas de subasta para asegurar que solo el creador de una subasta o un administrador pueda modificarla.

### `IsAdminOrReadOnly` (`permissions.py`)

**Descripción**: Permite a cualquiera realizar operaciones de lectura, pero restringe operaciones de escritura a administradores.

**Implementación**:
```python
def has_permission(self, request, view):
    # Permitir GET, HEAD, OPTIONS a cualquier usuario
    if request.method in permissions.SAFE_METHODS:
        return True
    
    # Solo administradores pueden modificar
    return request.user and request.user.is_staff
```

**Uso**: Aplicado en vistas de categorías y otras entidades donde solo los administradores deben poder crear/modificar.

### `IsPujaOwnerOrAdmin` (`permissions.py`)

**Descripción**: Permite gestionar pujas solo a su creador o a administradores.

**Implementación**:
```python
def has_object_permission(self, request, view, obj):
    # Administradores tienen acceso completo
    if request.user.is_staff:
        return True
    
    # Solo el pujador puede modificar/eliminar su puja
    return obj.pujador == request.user
```

**Uso**: Asegura que un usuario solo pueda modificar o eliminar sus propias pujas.

### `IsComentarioOwnerOrAdmin` (`permissions.py`)

**Descripción**: Permite gestionar comentarios solo a su autor o a administradores.

**Implementación**: Similar a `IsPujaOwnerOrAdmin` pero para comentarios.

**Uso**: Asegura que un usuario solo pueda modificar o eliminar sus propios comentarios.

## Flujos de datos comunes

A continuación se detallan algunos flujos de datos comunes y cómo interactúan los componentes del sistema:

### Creación de una subasta

1. El usuario envía una solicitud POST a `/api/subastas/` con los datos de la subasta
2. La vista `SubastaListCreate` recibe la solicitud
3. El serializador `SubastaSerializer` valida los datos:
   - Verifica que la fecha de cierre sea al menos 15 días en el futuro
   - Valida que el precio inicial sea positivo
   - Asegura que el stock sea al menos 1
4. Si la validación es exitosa, se crea un nuevo objeto `Subasta` en la base de datos
5. La subasta se asocia automáticamente al usuario autenticado (campo `usuario`)
6. Se devuelve el objeto serializado con status 201 (Created)

### Proceso de puja

1. El usuario envía una solicitud POST a `/api/subastas/<id_subasta>/pujas/` con el monto de la puja
2. La vista `PujaListCreate` recibe la solicitud
3. La vista verifica que la subasta exista y esté abierta
4. El serializador `PujaSerializer` valida el monto:
   - Si no hay pujas previas, debe ser mayor que el precio inicial
   - Si hay pujas previas, debe ser mayor que la puja más alta actual
5. Se crea un nuevo objeto `Puja` asociado a la subasta y al usuario
6. Se retorna la puja serializada con status 201 (Created)

### Actualización del estado de una subasta

El sistema verifica automáticamente el estado de una subasta cuando se accede a ella:

1. Cuando cualquier vista relacionada con subastas o pujas se accede, se verifica la fecha de cierre
2. Si la fecha de cierre ha pasado y el estado aún es 'abierta', se actualiza a 'cerrada'
3. Este cambio afecta inmediatamente a las operaciones, impidiendo nuevas pujas

## Validaciones y reglas de negocio

El sistema implementa múltiples validaciones para mantener la integridad de los datos:

### Subastas

- **Fecha de cierre**: Debe ser al menos 15 días después de la fecha actual
- **Precio inicial**: Debe ser un valor positivo mayor que cero
- **Stock**: Debe ser al menos 1
- **Valoración**: Debe estar en el rango de 1 a 5

### Pujas

- **Monto**: Debe ser mayor que el precio inicial (si es la primera puja) o mayor que la puja más alta actual
- **Estado de subasta**: Solo se permiten pujas en subastas abiertas
- **Modificación/eliminación**: Solo permitido al autor de la puja y en subastas abiertas

### Valoraciones

- **Valor**: Debe estar en el rango de 1 a 5
- **Unicidad**: Un usuario solo puede tener una valoración por subasta
- **Cascada**: Al eliminar una valoración, se recalcula automáticamente la valoración media de la subasta

## Ejemplos de uso de la API

A continuación se presentan algunos ejemplos de cómo interactuar con la API utilizando curl:

### Registro de usuario

```bash
curl -X POST http://localhost:8000/api/usuarios/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo_usuario",
    "email": "usuario@example.com",
    "password": "Clave1234",
    "password2": "Clave1234",
    "first_name": "Nombre",
    "last_name": "Apellido",
    "birth_date": "1990-01-01",
    "municipality": "Madrid",
    "locality": "Centro"
  }'
```

**Explicación del flujo**:
1. La solicitud llega a `UserRegisterView`
2. `UserSerializer` valida los datos, incluida la coincidencia de contraseñas
3. Se crea un nuevo usuario con la contraseña hasheada
4. Se generan tokens JWT para el usuario
5. Se devuelve la respuesta con los datos del usuario y los tokens

### Iniciar sesión (obtener token)

```bash
curl -X POST http://localhost:8000/api/token/ \
  -H "Content-Type: application/json" \
  -d '{
    "username": "nuevo_usuario",
    "password": "Clave1234"
  }'
```

**Explicación del flujo**:
1. La solicitud llega a `CustomTokenObtainPairView`
2. `CustomTokenObtainPairSerializer` valida las credenciales
3. Si son correctas, genera un token de acceso y un token de refresco
4. Devuelve ambos tokens junto con el nombre de usuario

### Crear una subasta (autenticado)

```bash
curl -X POST http://localhost:8000/api/subastas/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_de_acceso>" \
  -d '{
    "titulo": "iPhone 13 Pro Max",
    "descripcion": "Smartphone Apple en perfecto estado",
    "precio_inicial": 500,
    "fecha_cierre": "2023-12-31T23:59:59Z",
    "stock": 1,
    "categoria": 1
  }'
```

**Explicación del flujo**:
1. La solicitud llega a `SubastaListCreate.post`
2. Se verifica el token JWT para autenticar al usuario
3. `SubastaSerializer` valida los datos según las reglas de negocio
4. Se crea una nueva subasta asociada al usuario autenticado
5. Se inicializa con estado 'abierta' y fecha de creación actual
6. Se devuelve la subasta creada, incluyendo información calculada como precio_actual

### Realizar una puja

```bash
curl -X POST http://localhost:8000/api/subastas/1/pujas/ \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer <token_de_acceso>" \
  -d '{
    "cantidad": 550
  }'
```

**Explicación del flujo**:
1. La solicitud llega a `PujaListCreate.post`
2. Se verifica el token JWT para autenticar al usuario
3. La vista verifica si la subasta existe y está abierta
4. `PujaSerializer` valida que la cantidad sea mayor que la puja más alta o el precio inicial
5. Se crea una nueva puja asociada al usuario y a la subasta
6. Se devuelve la puja creada con información del pujador

## Manejo de modelos relacionados

El sistema utiliza relaciones entre modelos para mantener la integridad referencial:

### Relación Subasta-Usuario

- Un usuario puede crear múltiples subastas
- La subasta almacena una clave foránea al usuario creador
- Implementado como `usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)`

### Relación Puja-Subasta-Usuario

- Una subasta puede tener múltiples pujas
- Una puja pertenece a una única subasta y un único usuario
- Implementado como:
  - `subasta = models.ForeignKey(Subasta, related_name='pujas', on_delete=models.CASCADE)`
  - `pujador = models.ForeignKey(CustomUser, on_delete=models.CASCADE)`

### Relación Rating-Subasta-Usuario

- Una subasta puede tener múltiples valoraciones
- Un usuario solo puede valorar una vez cada subasta
- Implementado como:
  - `subasta = models.ForeignKey(Subasta, related_name='ratings', on_delete=models.CASCADE)`
  - `usuario = models.ForeignKey(CustomUser, on_delete=models.CASCADE)`
  - Se valida la unicidad a nivel de aplicación en el método `perform_create`

## Datos de prueba

El script `populate_db.py` crea datos de ejemplo para probar la aplicación:

- 1 administrador (admin/Admin2025)
- 4 usuarios normales
- 3 categorías diferentes
- 10 subastas de ejemplo
- Múltiples pujas, valoraciones y comentarios

## Despliegue en producción

Para desplegar en producción, se recomienda:

1. Cambiar `settings.py` para usar la configuración de PostgreSQL
2. Configurar variables de entorno para credenciales
3. Desactivar el modo DEBUG
4. Usar un servidor WSGI como Gunicorn
5. Configurar un servidor web como Nginx como proxy

## Solución de problemas comunes

### Error 401 (Unauthorized)

- **Causa posible**: Token JWT expirado o inválido
- **Solución**: Refresca el token o inicia sesión nuevamente con:
  ```bash
  curl -X POST http://localhost:8000/api/token/refresh/ \
    -H "Content-Type: application/json" \
    -d '{"refresh": "<token_de_refresco>"}'
  ```

### Error 403 (Forbidden)

- **Causa posible**: No tienes los permisos necesarios para esta acción
- **Solución**: Verifica que seas propietario del recurso o administrador

### Error en migración de base de datos

- **Solución**: Intenta ejecutar `python manage.py migrate --fake-initial` y luego ejecuta las migraciones normalmente

## Contribuciones

Las contribuciones son bienvenidas. Por favor, sigue estos pasos:

1. Haz un fork del repositorio
2. Crea una rama para tu característica (`git checkout -b feature/nueva-caracteristica`)
3. Realiza tus cambios
4. Ejecuta las pruebas (`python manage.py test`)
5. Haz commit de tus cambios (`git commit -m 'Añadir nueva característica'`)
6. Envía un pull request

## Licencia

Este proyecto está licenciado bajo [Licencia MIT](LICENSE)

## Contacto

Para preguntas o soporte, por favor contacta al equipo de desarrollo en: pacomprar@example.com
 
