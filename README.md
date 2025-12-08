# 🎰 BLACKJACK ROGUELITE - ETAPA 2

## Sistema de Garitos + Trampas + Objetos

```
╔═══════════════════════════════════════════════════════════════╗
║     "La suerte favorece a los que hacen trampa"               ║
╚═══════════════════════════════════════════════════════════════╝
```

---

## 🎮 CARACTERÍSTICAS NUEVAS

### 🏚️ Sistema de Garitos (5 niveles)

| # | Garito | Crupier | Meta | Detección | Regla Especial |
|---|--------|---------|------|-----------|----------------|
| 1 | El Callejón de los Desahuciados | Manco Pete | $1,000 | 15% | - |
| 2 | La Taberna del Tuerto | Sally la Sorda | $2,500 | 25% | +10% ganancias |
| 3 | El Salón Dorado | Don Rodrigo | $5,000 | 35% | Doblar paga 2.5x |
| 4 | La Casa de la Viuda Negra | La Viuda | $10,000 | 45% | Empates = Derrotas |
| 5 | El Infierno de Dante | El Diablo | ∞ | 60% | BJ dealer = pierdes todo |

### 🃏 Sistema de Trampas

| Trampa | Efecto | Estrés | Desbloqueo |
|--------|--------|--------|------------|
| 👁️ Espiar Carta | Ver carta oculta del crupier | +5 | Inicio |
| 🔄 Cambiar Carta | Cambia tu peor carta | +15 | Garito 2 |
| 🃏 Carta Extra | Roba sin contar como Hit | +20 | Garito 3 |
| ✒️ Marcar Mazo | Ve las próximas 3 cartas | +10 | Garito 4 |
| 💰 Sobornar | El crupier "se equivoca" | +25 + $50 | Especial |

**⚠️ RIESGO:** Si te pillan haciendo trampa, pierdes la apuesta actual y ganas +15 estrés.

### 📦 Tienda de Objetos

| Objeto | Precio | Efecto |
|--------|--------|--------|
| 🥃 Whiskey Barato | $25 | -10 estrés |
| 🚬 Cigarro de la Suerte | $75 | Próxima trampa 100% éxito |
| 🎲 Dado Cargado | $100 | +5% probabilidad BJ |
| 🕶️ Gafas Oscuras | $200 | -10% detección (permanente) |
| 💍 Anillo con Sello | $300 | +15% ganancias (permanente) |
| ⏱️ Reloj de Bolsillo | $500 | Repite última ronda (1/garito) |

### 😰 Barra de Estrés

- Máximo: 100
- Hacer trampas aumenta estrés
- Ser detectado: +15 estrés extra
- Ganar: -5 estrés
- Perder: +3 estrés
- **Si llegas a 100: GAME OVER (colapso nervioso)**

---

## 🚀 CÓMO EJECUTAR

### Backend (Python)

```bash
cd backend
pip install -r requirements.txt
python main.py
```

El servidor estará en `http://localhost:8000`

### Frontend (React)

El archivo `App.jsx` está diseñado para funcionar con cualquier setup de React.

**Opción 1: Create React App**
```bash
npx create-react-app blackjack-roguelite
cd blackjack-roguelite
# Reemplaza src/App.jsx con el archivo proporcionado
npm start
```

**Opción 2: Vite**
```bash
npm create vite@latest blackjack-roguelite -- --template react
cd blackjack-roguelite
# Reemplaza src/App.jsx con el archivo proporcionado
npm install
npm run dev
```

---

## 📡 API Endpoints

### Básicos
```
POST /games              → Crear partida
GET  /games/{id}         → Estado actual
POST /games/{id}/bet     → Apostar
POST /games/{id}/action  → hit/stand/double
POST /games/{id}/new-round → Nueva mano
DELETE /games/{id}       → Salir
```

### Nuevos (Etapa 2)
```
POST /games/{id}/cheat         → Intentar trampa
POST /games/{id}/use-item      → Usar objeto
POST /games/{id}/buy-item      → Comprar en tienda
POST /games/{id}/advance-garito → Avanzar de garito
POST /games/{id}/leave-shop    → Salir de tienda
GET  /meta/garitos             → Info de garitos
GET  /meta/cheats              → Info de trampas
GET  /meta/items               → Info de objetos
```

---

## 🎯 ESTRATEGIA

1. **Empieza conservador** - Aprende los patrones del crupier
2. **Usa trampas con moderación** - El estrés se acumula
3. **Compra Gafas Oscuras temprano** - La reducción de detección es permanente
4. **Guarda el Cigarro** - Para momentos críticos
5. **El Whiskey es tu amigo** - Mantén el estrés bajo control
6. **Cuidado con La Viuda** - Los empates duelen
7. **El Diablo no perdona** - Su BJ te arruina

---

## 📝 PRÓXIMAS MEJORAS (Etapa 3)

- [ ] Sonidos (beeps de terminal)
- [ ] Eventos aleatorios entre rondas
- [ ] Sistema de logros
- [ ] Guardado de partida
- [ ] Más trampas avanzadas
- [ ] Crupiers con personalidades únicas

---

```
                    ♠ ♥ ♣ ♦
        "En el Callejón, todos hacen trampa.
         La diferencia es quién no lo pillan."
                    ♦ ♣ ♥ ♠
```
