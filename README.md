# PROPUESTA DE DISEÑO: BLACKJACK RPG ROGUELITE (TERMINAL EDITION)

## 1. CONCEPTO GENERAL
Un juego de progresión roguelite con estética oscura tipo DOS. El jugador recorre garitos clandestinos enfrentándose a oponentes pícaros. Combina la mecánica del Blackjack con un sistema de habilidades, gestión de estrés y el apoyo de mascotas mágicas.

## 2. ARQUITECTURA TÉCNICA
* **Backend (Python/FastAPI):** Lógica del mazo, motor de probabilidades, gestión de la banca del Capo y validación de trampas.
* **Frontend (Vue.js 3):** Interfaz reactiva emulando una terminal CRT, gestión de estado (Pinia) y efectos visuales ASCII.
* **Base de Datos (PostgreSQL):** Persistencia de objetos, desbloqueos permanentes y estadísticas de incursión.

## 3. MECÁNICAS DE JUEGO
### 3.1. El Acompañante: El Goblin Mágico
* **Habilidad de Transmutación:** Permite transformar una carta una vez por partida.
* **Evolución:** Mejora con el uso, permitiendo "espiar" la carta oculta o reducir el coste de estrés de las habilidades.

### 3.2. Sistema de Estrés y Juego Sucio
* **Juego Sucio:** Mecánica para robar cartas extra o intercambiar valores. Su éxito depende de la Percepción del crupier.
* **Estrés:** Barra de salud mental. Las pérdidas fuertes y las trampas fallidas aumentan el estrés. Al 100%, el jugador sufre una derrota crítica.

## 4. ENTORNOS (GARITOS) TEMÁTICOS
### 4.1. El Bar de Motoqueros "Escape Libre"
* **Regla:** Apuesta de Motor. Si pierdes la apuesta, el estrés aumenta permanentemente por la pérdida del vehículo.
### 4.2. La Taberna del Mago "El Cáliz Roto"
* **Regla:** Mazo Mutante. Los valores de las cartas cambian aleatoriamente cada tres manos.
### 4.3. La Hacienda (Mansión del Capo)
* **Regla:** "La Banca Nunca Pierde". Si el Capo tiene pocos fondos, es imposible sacar Blackjack natural.
* **Derrota Crítica:** Ser detectado haciendo trampa resulta en eliminación inmediata (Plomo).
### 4.4. El Callejón de los Desahuciados
* **Regla:** Mazo Desgastado. Algunas cartas son ilegibles (?) y requieren deducción por conteo.

## 5. GESTIÓN DE PATRIMONIO
* **Crédito Callejero:** Nivel de experiencia y moneda para desbloquear garitos.
* **Objetos de Valor:** Reliquias que otorgan ventajas pasivas (ej. Reloj de Oro que reduce el estrés por turno).

## 6. ESQUEMA DE BASE DE DATOS ACTUALIZADO
### Tabla: Mascotas (Pets)
* id (UUID)
* player_id (FK)
* tipo (Goblin/Cuervo/Rata)
* nivel (Integer)
* afinidad (Integer)

### Tabla: Garitos_Desbloqueados (Unlocked_Venues)
* id (UUID)
* player_id (FK)
* garito_nombre (String)
* record_ganancias (Integer)

### Tabla: Inventario_Permanente (Permanent_Inventory)
* id (UUID)
* player_id (FK)
* item_id (UUID)
* equipado (Boolean)