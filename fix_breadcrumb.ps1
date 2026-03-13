$base = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  FIX BREADCRUMB POSITION + BOUTONS     " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ============================================================
# ETAPE 1 : Remplacer breadcrumb.html avec le bon positionnement
# Le breadcrumb s'affiche maintenant SOUS le header rouge
# grace au CSS (order dans flex) - sans toucher aux templates
# ============================================================

$htmlPath = "$base\templates\components\breadcrumb.html"
$htmlLines = @(
    "{# templates/components/breadcrumb.html #}",
    "{# S'utilise DANS le block content, apres le page-header #}",
    "<nav class=""behanian-breadcrumb"" aria-label=""breadcrumb"">",
    "    <div class=""bc-inner"">",
    "        <a href=""{% url 'dashboard:index' %}"" class=""bc-home"" title=""Accueil"">",
    "            <i class=""fas fa-home""></i>",
    "        </a>",
    "        {% for item in items %}",
    "            <span class=""bc-sep"">&#x203A;</span>",
    "            {% if item.active %}",
    "                <span class=""bc-current"">{{ item.label }}</span>",
    "            {% else %}",
    "                <a href=""{{ item.url }}"" class=""bc-link"">{{ item.label }}</a>",
    "            {% endif %}",
    "        {% endfor %}",
    "    </div>",
    "</nav>",
    "<style>",
    ".behanian-breadcrumb { margin-bottom: 16px; margin-top: 0; }",
    ".bc-inner { display: inline-flex; align-items: center; gap: 6px; background: white; border: 1px solid #f0f0f0; border-radius: 30px; padding: 7px 16px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); font-size: 0.84rem; flex-wrap: wrap; }",
    ".bc-home { color: #c0392b; text-decoration: none; font-size: 0.9rem; display: flex; align-items: center; transition: color 0.2s; }",
    ".bc-home:hover { color: #e74c3c; }",
    ".bc-sep { color: #d0d0d0; font-size: 0.9rem; font-weight: 300; user-select: none; }",
    ".bc-link { color: #c0392b; text-decoration: none; font-weight: 600; transition: color 0.2s; }",
    ".bc-link:hover { color: #e74c3c; text-decoration: underline; }",
    ".bc-current { color: #2d3748; font-weight: 700; }",
    "</style>"
)
[System.IO.File]::WriteAllLines($htmlPath, $htmlLines, [System.Text.Encoding]::UTF8)
Write-Host "[OK] breadcrumb.html mis a jour" -ForegroundColor Green

# ============================================================
# ETAPE 2 : Dans chaque template cuisine,
#   - Deplacer le breadcrumb apres le page-header
#   - Supprimer les boutons retour
# ============================================================

$templates = @(
    "templates\cuisine\stock_management.html",
    "templates\cuisine\ingredient_form.html",
    "templates\cuisine\bon_commande_form.html",
    "templates\cuisine\bon_reception_form.html",
    "templates\cuisine\inventaire_form.html",
    "templates\cuisine\casse_form.html",
    "templates\cuisine\index.html"
)

foreach ($tplRel in $templates) {
    $filePath = "$base\$tplRel"
    if (-not (Test-Path $filePath)) {
        Write-Host "[INFO] Pas encore cree : $tplRel" -ForegroundColor DarkGray
        continue
    }

    $lines = [System.IO.File]::ReadAllLines($filePath, [System.Text.Encoding]::UTF8)
    $newLines = [System.Collections.Generic.List[string]]::new()

    $bcLine = ""
    $insideHeader = $false
    $headerDivDepth = 0
    $headerClosed = $false
    $bcInserted = $false
    $skipNextBlank = $false

    # --- Passe 1 : extraire la ligne breadcrumb ---
    foreach ($line in $lines) {
        if ($line -match "{% breadcrumb ") {
            $bcLine = $line.Trim()
            break
        }
    }

    if ($bcLine -eq "") {
        Write-Host "[SKIP] Pas de breadcrumb dans : $tplRel" -ForegroundColor Yellow
        continue
    }

    # --- Passe 2 : reconstruire le fichier ---
    foreach ($line in $lines) {

        # Sauter l'ancienne ligne breadcrumb (juste apres block content)
        if ($line -match "{% breadcrumb " -and -not $headerClosed) {
            continue
        }

        # Detecter ouverture du page-header
        if ($line -match 'class="page-header"' -or $line -match "class='page-header'") {
            $insideHeader = $true
            $headerDivDepth = 0
        }

        # Compter les div si dans le header
        if ($insideHeader) {
            $opens  = ([regex]::Matches($line, "<div")).Count
            $closes = ([regex]::Matches($line, "</div>")).Count
            $headerDivDepth += $opens - $closes

            # Quand on retombe a 0 ou moins, le header est ferme
            if ($headerDivDepth -le 0 -and ($line -match "</div>")) {
                $insideHeader = $false
                $headerClosed = $true
                $newLines.Add($line)
                # Inserer le breadcrumb juste apres la fermeture du header
                $newLines.Add("    $bcLine")
                $bcInserted = $true
                continue
            }
        }

        # Supprimer les boutons retour (back-link, btn-back, chevron-left seul)
        if ($line -match 'class="back-link' -or $line -match "class='back-link" -or
            $line -match 'class="btn-back'  -or $line -match "class='btn-back"  -or
            ($line -match 'fa-chevron-left' -and $line -match '<a ')) {
            continue
        }

        $newLines.Add($line)
    }

    if ($bcInserted) {
        [System.IO.File]::WriteAllLines($filePath, $newLines.ToArray(), [System.Text.Encoding]::UTF8)
        Write-Host "[OK] Corrige : $tplRel" -ForegroundColor Green
    } else {
        Write-Host "[WARN] Header non trouve, fichier non modifie : $tplRel" -ForegroundColor Red
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  CORRECTIONS TERMINEES !               " -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Redemarrer le serveur :" -ForegroundColor White
Write-Host "  Stop-Process -Name python -Force" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Yellow
Write-Host ""
