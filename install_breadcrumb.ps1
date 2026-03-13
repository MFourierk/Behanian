$base = "D:\Doc\Biz\Projet Behanian\Claude\Behanian_Project"

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION BREADCRUMB - BEHANIAN    " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$compDir = "$base\templates\components"
if (-not (Test-Path $compDir)) {
    New-Item -ItemType Directory -Path $compDir | Out-Null
    Write-Host "[OK] Dossier cree : templates\components" -ForegroundColor Green
} else {
    Write-Host "[OK] Dossier existe : templates\components" -ForegroundColor Yellow
}

$htmlPath = "$compDir\breadcrumb.html"
$htmlLines = @(
    "{# templates/components/breadcrumb.html #}",
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
    ".behanian-breadcrumb { margin-bottom: 20px; margin-top: 6px; }",
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
Write-Host "[OK] Fichier cree : templates\components\breadcrumb.html" -ForegroundColor Green

$pyPath = "$base\dashboard\templatetags\breadcrumb.py"
$pyLines = @(
    "from django import template",
    "from django.urls import reverse, NoReverseMatch",
    "",
    "register = template.Library()",
    "",
    "",
    "@register.inclusion_tag('components/breadcrumb.html', takes_context=True)",
    "def breadcrumb(context, *args):",
    "    items = []",
    "    args = list(args)",
    "    while len(args) >= 2:",
    "        label    = args.pop(0)",
    "        url_name = args.pop(0)",
    "        if url_name:",
    "            try:",
    "                url = reverse(url_name)",
    "                items.append({'label': label, 'url': url, 'active': False})",
    "            except NoReverseMatch:",
    "                items.append({'label': label, 'url': url_name, 'active': False})",
    "        else:",
    "            items.append({'label': label, 'url': None, 'active': True})",
    "    return {'items': items}",
    "",
    "",
    "@register.inclusion_tag('components/breadcrumb.html')",
    "def breadcrumb_items(items):",
    "    return {'items': items}"
)
[System.IO.File]::WriteAllLines($pyPath, $pyLines, [System.Text.Encoding]::UTF8)
Write-Host "[OK] Fichier cree : dashboard\templatetags\breadcrumb.py" -ForegroundColor Green

$initPath = "$base\dashboard\templatetags\__init__.py"
if (-not (Test-Path $initPath)) {
    New-Item -ItemType File -Path $initPath | Out-Null
    Write-Host "[OK] Fichier cree : dashboard\templatetags\__init__.py" -ForegroundColor Green
} else {
    Write-Host "[OK] Existe deja : dashboard\templatetags\__init__.py" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "--- Ajout dans les templates cuisine ---" -ForegroundColor Cyan

$templates = @{
    "templates\cuisine\index.html"              = "{% breadcrumb `"Cuisine`" `"`" %}"
    "templates\cuisine\stock_management.html"   = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Stock`" `"`" %}"
    "templates\cuisine\ingredient_form.html"    = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Stock`" `"cuisine:stock_management`" `"Ingredient`" `"`" %}"
    "templates\cuisine\bon_commande_form.html"  = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Commandes`" `"cuisine:stock_management`" `"Bon de Commande`" `"`" %}"
    "templates\cuisine\bon_reception_form.html" = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Receptions`" `"cuisine:stock_management`" `"Nouvelle Reception`" `"`" %}"
    "templates\cuisine\inventaire_form.html"    = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Stock`" `"cuisine:stock_management`" `"Inventaire`" `"`" %}"
    "templates\cuisine\casse_form.html"         = "{% breadcrumb `"Cuisine`" `"cuisine:index`" `"Stock`" `"cuisine:stock_management`" `"Declarer une Casse`" `"`" %}"
}

foreach ($tpl in $templates.GetEnumerator()) {
    $filePath = "$base\$($tpl.Key)"
    if (Test-Path $filePath) {
        $content = Get-Content $filePath -Raw -Encoding UTF8
        if ($content -match "breadcrumb") {
            Write-Host "[SKIP] Deja present : $($tpl.Key)" -ForegroundColor Yellow
            continue
        }
        $loadTag = "{% load breadcrumb %}"
        $bcTag = $tpl.Value
        if ($content -notmatch "{% load breadcrumb %}") {
            $content = $content -replace "({% extends [^%]+%})", "`$1`n$loadTag"
        }
        if ($content -match "{% block content %}") {
            $content = $content -replace "({% block content %})", "`$1`n$bcTag"
        }
        [System.IO.File]::WriteAllText($filePath, $content, [System.Text.Encoding]::UTF8)
        Write-Host "[OK] Breadcrumb ajoute : $($tpl.Key)" -ForegroundColor Green
    } else {
        Write-Host "[INFO] Template pas encore cree : $($tpl.Key)" -ForegroundColor DarkGray
    }
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  INSTALLATION TERMINEE !" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""
Write-Host "Redemarrer le serveur :" -ForegroundColor White
Write-Host "  Stop-Process -Name python -Force" -ForegroundColor Yellow
Write-Host "  python manage.py runserver" -ForegroundColor Yellow
Write-Host ""
