def generar_carta_svg(valor, palo, ancho=180, alto=250):
    """
    Genera una carta de poker/blackjack en formato SVG.
    
    Args:
        valor: '2'-'10', 'J', 'Q', 'K', 'A'
        palo: 'corazones', 'picas', 'diamantes', 'treboles'
        ancho: ancho de la carta en pixels
        alto: alto de la carta en pixels
    
    Returns:
        String con el código SVG completo
    """
    
    # Símbolos SVG de cada palo (centrados en 0,0)
    SIMBOLOS = {
        'corazones': '''<path d="M 0,-8 C -4,-12 -10,-12 -10,-6 C -10,0 0,8 0,8 C 0,8 10,0 10,-6 C 10,-12 4,-12 0,-8 Z"/>''',
        
        'picas': '''<path d="M 0,-10 C -3,-6 -8,-2 -8,2 C -8,5 -6,7 -3,7 L -4,11 C -4,12 -3,13 -2,13 L 2,13 C 3,13 4,12 4,11 L 3,7 C 6,7 8,5 8,2 C 8,-2 3,-6 0,-10 Z"/>''',
        
        'diamantes': '''<path d="M 0,-10 L 7,0 L 0,10 L -7,0 Z"/>''',
        
        'treboles': '''<g>
            <circle cx="0" cy="-4" r="4"/>
            <circle cx="-4" cy="2" r="4"/>
            <circle cx="4" cy="2" r="4"/>
            <path d="M -2,5 L -3,11 C -3,12 -2,13 -1,13 L 1,13 C 2,13 3,12 3,11 L 2,5"/>
        </g>'''
    }
    
    # Colores según el palo
    colores = {
        'corazones': '#D32F2F',
        'diamantes': '#D32F2F',
        'picas': '#212121',
        'treboles': '#212121'
    }
    
    color = colores.get(palo, '#000000')
    simbolo = SIMBOLOS.get(palo, '')
    
    # Posiciones de símbolos centrales según el valor
    posiciones = {
        'A': [(ancho/2, alto*0.5)],
        '2': [(ancho/2, alto*0.3), (ancho/2, alto*0.7)],
        '3': [(ancho/2, alto*0.25), (ancho/2, alto*0.5), (ancho/2, alto*0.75)],
        '4': [(ancho*0.35, alto*0.3), (ancho*0.65, alto*0.3), 
              (ancho*0.35, alto*0.7), (ancho*0.65, alto*0.7)],
        '5': [(ancho*0.35, alto*0.3), (ancho*0.65, alto*0.3), (ancho/2, alto*0.5),
              (ancho*0.35, alto*0.7), (ancho*0.65, alto*0.7)],
        '6': [(ancho*0.35, alto*0.27), (ancho*0.65, alto*0.27),
              (ancho*0.35, alto*0.5), (ancho*0.65, alto*0.5),
              (ancho*0.35, alto*0.73), (ancho*0.65, alto*0.73)],
        '7': [(ancho*0.35, alto*0.27), (ancho*0.65, alto*0.27),
              (ancho/2, alto*0.38), 
              (ancho*0.35, alto*0.5), (ancho*0.65, alto*0.5),
              (ancho*0.35, alto*0.73), (ancho*0.65, alto*0.73)],
        '8': [(ancho*0.35, alto*0.27), (ancho*0.65, alto*0.27),
              (ancho/2, alto*0.35),
              (ancho*0.35, alto*0.5), (ancho*0.65, alto*0.5),
              (ancho/2, alto*0.65),
              (ancho*0.35, alto*0.73), (ancho*0.65, alto*0.73)],
        '9': [(ancho*0.35, alto*0.25), (ancho*0.65, alto*0.25),
              (ancho*0.35, alto*0.4), (ancho*0.65, alto*0.4),
              (ancho/2, alto*0.5),
              (ancho*0.35, alto*0.6), (ancho*0.65, alto*0.6),
              (ancho*0.35, alto*0.75), (ancho*0.65, alto*0.75)],
        '10': [(ancho*0.35, alto*0.25), (ancho*0.65, alto*0.25),
               (ancho/2, alto*0.32),
               (ancho*0.35, alto*0.42), (ancho*0.65, alto*0.42),
               (ancho*0.35, alto*0.58), (ancho*0.65, alto*0.58),
               (ancho/2, alto*0.68),
               (ancho*0.35, alto*0.75), (ancho*0.65, alto*0.75)],
        'J': [(ancho/2, alto/2)],
        'Q': [(ancho/2, alto/2)],
        'K': [(ancho/2, alto/2)]
    }
    
    # Determinar qué símbolos rotar 180°
    def simbolos_a_rotar(valor):
        if valor in ['J', 'Q', 'K', 'A']:
            return []
        elif valor in ['2', '3']:
            return [1]  # Solo el segundo símbolo
        elif valor in ['4', '5', '6', '7', '8', '9', '10']:
            # Rotar la mitad inferior
            total = len(posiciones[valor])
            #return list(range(total // 2, total))
        return []
    
    rotados = simbolos_a_rotar(valor)
    
    # Iniciar SVG
    svg = f'''<svg width="{ancho}" height="{alto}" xmlns="http://www.w3.org/2000/svg">
    <!-- Marco de la carta -->
    <rect x="2" y="2" width="{ancho-4}" height="{alto-4}" 
          fill="white" stroke="#333" stroke-width="2" rx="10"/>
    
    <!-- Valor esquina superior izquierda -->
    <text x="15" y="30" font-family="Arial, sans-serif" font-size="24" 
          font-weight="bold" fill="{color}">{valor}</text>
    <g transform="translate(15, 40)" fill="{color}">
        {simbolo}
    </g>
    
    <!-- Valor esquina inferior derecha (invertido) -->
    <g transform="rotate(180, {ancho/2}, {alto/2})">
        <text x="15" y="30" font-family="Arial, sans-serif" font-size="24" 
              font-weight="bold" fill="{color}">{valor}</text>
        <g transform="translate(15, 40)" fill="{color}">
            {simbolo}
        </g>
    </g>
    
    <!-- Símbolos centrales -->
    <g fill="{color}">'''
    
    # Agregar símbolos según el valor
    if valor in posiciones:
        for i, (x, y) in enumerate(posiciones[valor]):
            # Para figuras (J, Q, K) hacer símbolo más grande
            if valor in ['J', 'Q', 'K']:
                escala = 4.0
            elif valor == 'A':
                escala = 3.5
            else:
                escala = 1.8
            
            # Rotar símbolos de la mitad inferior
            rotacion = 180 if i in rotados else 0
            
            svg += f'''
        <g transform="translate({x}, {y}) scale({escala}) rotate({rotacion})">
            {simbolo}
        </g>'''
    
    svg += '''
    </g>
</svg>'''
    
    return svg


# Ejemplos de uso
if __name__ == "__main__":
    # Generar algunas cartas de ejemplo
    cartas = [
        ("A", "corazones"),
        ("A", "picas"),
        ("K", "diamantes"),
        ("7", "treboles"),
        ("10", "corazones"),
        ("Q", "picas"),
        ("5", "diamantes")
    ]
    
    for valor, palo in cartas:
        svg = generar_carta_svg(valor, palo)
        nombre_archivo = f"carta_{valor}_{palo}.svg"
        with open(nombre_archivo, "w", encoding="utf-8") as f:
            f.write(svg)
        print(f"Generada: {nombre_archivo}")
    
    # También puedes usar la función para obtener el SVG como string
    carta_as = generar_carta_svg("A", "picas")
    print("\nEjemplo de SVG generado:")
    print(carta_as)