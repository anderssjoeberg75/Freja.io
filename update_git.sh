#!/bin/bash
# upload_freja.sh (Korrigerad version)
# Script för att ladda upp filer till github.com/anderssjoeberg75/Freja.io

# Konfiguration
REPO_URL="https://github.com/anderssjoeberg75/Freja.io.git"
BRANCH="main"
COMMIT_MSG="Update: $(date '+%Y-%m-%d %H:%M:%S')"

# 1. Kontrollera git
if ! command -v git &> /dev/null; then
    echo "❌ Git är inte installerat."
    exit 1
fi

echo "🚀 Startar uppladdning till Freja.io..."

# 2. Initiera Git om det saknas
if [ ! -d ".git" ]; then
    echo "📂 Initierar nytt Git-repo..."
    git init
fi

# VIKTIGT: Byt alltid namn på nuvarande branch till 'main'
# Detta fixar 'refspec main does not match any' om du råkar stå på 'master'
git branch -M $BRANCH

# 3. Konfigurera Remote URL
CURRENT_REMOTE=$(git remote get-url origin 2>/dev/null || echo "")

if [ "$CURRENT_REMOTE" == "" ]; then
    echo "🔗 Lägger till remote origin..."
    git remote add origin $REPO_URL
elif [ "$CURRENT_REMOTE" != "$REPO_URL" ]; then
    echo "🔄 Uppdaterar remote origin..."
    git remote set-url origin $REPO_URL
fi

# 4. Lägg till filer och skapa commit
echo "📦 Lägger till alla filer..."
git add .

# Kolla status för att se om det finns något att committa
if git diff-index --quiet HEAD -- 2>/dev/null; then
    # Inga ändringar upptäcktes mot HEAD, men vi måste kolla om det är första committen (HEAD finns ej)
    if ! git rev-parse --verify HEAD >/dev/null 2>&1; then
         # HEAD saknas -> Första commit
         echo "💾 Skapar första commit..."
         git commit -m "First commit"
    else
         CHANGES=$(git status --porcelain)
         if [ -z "$CHANGES" ]; then
             echo "ℹ️ Inga nya ändringar att spara."
             # Vi fortsätter ändå till push ifall lokala commits inte är uppladdade än
         else
             echo "💾 Skapar commit..."
             git commit -m "$COMMIT_MSG"
         fi
    fi
else
    # Ändringar finns mot HEAD
    echo "💾 Skapar commit..."
    git commit -m "$COMMIT_MSG"
fi

# 5. Pusha till GitHub
echo "⬆️ Laddar upp till GitHub ($BRANCH)..."
git push -u origin $BRANCH

if [ $? -eq 0 ]; then
    echo "✅ Uppladdning klar! Koden finns nu på: $REPO_URL"
else
    echo "❌ Uppladdning misslyckades."
    echo "   Tips: Om du får 'permission denied', se till att du använder en SSH-nyckel eller Personal Access Token."
fi
