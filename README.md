# PROPUESTA DE DISEÑO: BLACKJACK RPG ROGUELITE

## 1. CONCEPTO GENERAL
Un juego de progresión roguuelite donde el jugador recorre distintos establecimientos clandestinos (garitos) enfrentándose a personajes pícaros en mesas de Blackjack. La progresión se basa en la mejora de habilidades, la gestión de patrimonio y la adaptación a reglas cambiantes.

## 2. ARQUITECTURA TÉCNICA
* **Backend (Python/FastAPI):** Encargado de la lógica de generación de mazos, validación de jugadas (prevención de trampas), gestión de probabilidades y persistencia de datos.
* **Frontend (Vue.js 3):** Interfaz reactiva para la representación visual de la mesa, animaciones de cartas y gestión del estado del jugador (Pinia).
* **Comunicación:** REST API para transacciones y WebSockets para eventos de juego en tiempo real.

## 3. MECÁNICAS DE JUEGO Y PROGRESIÓN
### 3.1. Sistema de Mazo Roguelite
* **Personalización:** El jugador añade cartas especiales a su mazo entre garitos.
* **Cartas de Habilidad:** Cartas con efectos como "No pasarse de 21 una vez por mano" o "Intercambiar carta con el crupier".

### 3.2. Gestión de Patrimonio y Salud
* **Crédito Callejero (Reputación):** Funciona como el nivel de experiencia. Permite acceder a garitos de apuestas más altas.
* **Objetos de Valor:** Bienes materiales que actúan como moneda de reserva o bonificadores de estadísticas.
* **Sistema de Estrés (Salud):** Barra que aumenta con las pérdidas consecutivas. Al llenarse, el jugador sufre una penalización o es expulsado de la incursión.

## 4. ENTORNOS Y PERSONAJES
### 4.1. Garitos y Reglas Particulares
* **El Sótano del Tuerto:** Mazo reducido de 40 cartas.
* **La Guarida del Gato Negro:** Los empates favorecen a la casa.
* **Casino Flotante:** Límite de pasarse extendido a 22, pero el crupier gana con 21 natural.

### 4.2. Los Pícaros (NPCs)
* **El Prestamista:** Ofrece fondos a cambio de reducir la salud máxima.
* **La Tahúr:** Capaz de cambiar una carta propia durante la partida.
* **Crupieres con Rasgos:** Patrones de comportamiento que revelan información sobre la carta oculta.

## 5. CONDICIONES DE VICTORIA Y DERROTA
* **Victoria:** Limpiar la mesa de un garito obteniendo el pase al siguiente nivel o derrotar al jefe final en el Gran Casino.
* **Derrota:** Bancarrota total (sin efectivo ni objetos) o colapso por estrés acumulado.

## 6. PROPUESTA DE ESQUEMA DE BASE DE DATOS (POSTGRESQL/SQLITE)
### Tabla: Jugador (Player)
* id (UUID)
* nombre (String)
* credito_callejero (Integer)
* estres_actual (Integer)
* estres_max (Integer)

### Tabla: Inventario (Inventory)
* id (UUID)
* player_id (FK)
* item_nombre (String)
* tipo (Consumible/Pasivo)
* efecto (JSON)

### Tabla: Estadísticas_Run (Run_Stats)
* id (UUID)
* player_id (FK)
* garitos_visitados (Integer)
* ganancia_total (Integer)
* estado (En_Curso/Finalizado)