SCENE_PROMPTS = {
    "personajes": [
        "el personaje principal del juego",
        "un enemigo normal",
        "un jefe final",
        "un personaje no jugable",
        "un aliado",
    ],
    "escenarios": [
        "un bosque",
        "una mazmorra",
        "una ciudad",
        "un desierto",
        "una cueva",
        "un castillo",
        "un campo abierto",
        "un templo",
    ],
    "efectos": [
        "una explosion",
        "fuego",
        "hielo",
        "un rayo",
        "magia",
        "humo",
    ],
    "estados": [
        "pantalla de muerte",
        "pantalla de victoria",
        "combate",
        "menu del juego",
        "pantalla de carga",
        "dialogo entre personajes",
    ],
    "ui": [
        "barra de vida",
        "barra de mana",
        "minimapa",
        "inventario",
        "botones de menu",
    ],
}

GAME_STATES = {
    "combate": ["combate", "peleando contra enemigos", "una batalla"],
    "exploracion": ["explorando", "caminando por el mapa", "viajando"],
    "menu": ["menu de opciones", "pantalla de pausa", "inventario"],
    "dialogo": ["personajes hablando", "conversacion", "dialogo"],
    "victoria": ["victoria", "nivel completado", "triunfo"],
    "derrota": ["game over", "has muerto", "pantalla de muerte"],
    "carga": ["pantalla de carga", "cargando", "loading"],
}
