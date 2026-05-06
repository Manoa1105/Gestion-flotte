/* =========================================================================
   tailwind.config.js - Configuration de Tailwind CSS
   =========================================================================
   Tailwind scanne les fichiers listés dans "content" pour détecter
   les classes utilisées (ex: "bg-blue-500"). Il génère ensuite UN SEUL
   fichier CSS contenant uniquement les classes nécessaires.

   Avantage : le CSS de prod fait ~15-30 Ko au lieu de ~340 Ko du CDN.
   Inconvénient : il faut relancer le build à chaque ajout de classe.
   ========================================================================= */

module.exports = {
    // Liste des fichiers à scanner pour détecter les classes Tailwind utilisées
    content: [
        './templates/**/*.html',
        './apps/**/templates/**/*.html',
    ],

    theme: {
        extend: {
            // Palette de couleurs personnalisée pour le projet
            // Style sobre et professionnel : blanc + bleu-gris
            colors: {
                primaire: {
                    50:  '#f0f5fb',
                    100: '#dbe7f3',
                    200: '#bdd0e8',
                    300: '#92b1d7',
                    400: '#658bc1',
                    500: '#456fae',  // Couleur principale
                    600: '#345893',
                    700: '#2c4878',
                    800: '#283e64',
                    900: '#253556',
                    950: '#192238',
                },
            },
            // Fonte personnalisée (on utilisera Inter, classique et lisible)
            fontFamily: {
                sans: ['Inter', 'system-ui', 'sans-serif'],
            },
        },
    },

    // Plugins additionnels
    plugins: [
        // Style amélioré par défaut pour les <input>, <select>, <textarea>
        require('@tailwindcss/forms'),
    ],
}
