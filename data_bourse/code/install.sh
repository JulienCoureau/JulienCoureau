#!/bin/bash

# Script d'installation pour l'Extracteur de Métriques Financières
# Author: Julien Coureau
# Date: 2025-11-28

echo "=========================================="
echo "Installation de l'Extracteur de Métriques"
echo "=========================================="
echo ""

# Vérifier que Python est installé
if ! command -v python3 &> /dev/null
then
    echo "❌ Python3 n'est pas installé!"
    echo "Veuillez installer Python 3.8 ou supérieur."
    exit 1
fi

echo "✓ Python détecté: $(python3 --version)"
echo ""

# Vérifier que pip est installé
if ! command -v pip3 &> /dev/null
then
    echo "❌ pip3 n'est pas installé!"
    echo "Veuillez installer pip3."
    exit 1
fi

echo "✓ pip détecté: $(pip3 --version)"
echo ""

# Installer les dépendances
echo "📦 Installation des dépendances Python..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✓ Dépendances installées avec succès"
else
    echo "❌ Erreur lors de l'installation des dépendances"
    exit 1
fi

echo ""
echo "=========================================="
echo "✅ Installation terminée avec succès!"
echo "=========================================="
echo ""
echo "Prochaines étapes:"
echo "1. Placez vos fichiers Excel dans: ~/documents/data_bourse/base_de_donnee/"
echo "2. Mettez à jour le fichier JSON dans: ~/documents/data_bourse/code/json_finance/"
echo "3. Exécutez: python3 extracteur_metriques.py"
echo ""
