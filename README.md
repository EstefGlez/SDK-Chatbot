# Base de datos — pendiente

Todavía no se decide entre Neon o Supabase (ver contexto.md). Cuando se decida:

1. Instalar el driver correspondiente (`psycopg` para Postgres directo, o el SDK de Supabase).
2. Crear aquí un `connection.py` con la conexión reutilizable.
3. Crear el esquema de las 4 tablas descritas en contexto.md: `chatbots`, `conversaciones`, `mensajes`, `feedback`.
4. Reemplazar los TODOs en `routers/chat.py` y `routers/admin.py` que hoy usan datos falsos/fijos, por consultas reales a estas tablas.
