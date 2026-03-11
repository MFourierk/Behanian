from django import forms
from .models import Ingredient, Fournisseur, CategorieIngredient, FicheTechnique, LigneFicheTechnique
from restaurant.models import PlatMenu, CategorieMenu


class RecetteModalForm(forms.Form):
    nom = forms.CharField(max_length=100, required=True, label="Nom du plat", widget=forms.TextInput(attrs={'class': 'form-control'}))
    categorie = forms.ModelChoiceField(queryset=CategorieMenu.objects.exclude(nom__in=['Boisson', 'Boissons']), required=True, widget=forms.Select(attrs={'class': 'form-select'}))
    description = forms.CharField(widget=forms.Textarea(attrs={'rows': 2, 'class': 'form-control'}), required=False)
    prix_vente = forms.DecimalField(max_digits=10, decimal_places=2, required=False, label="Prix de vente", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    nombre_portions = forms.IntegerField(initial=1, required=True, widget=forms.NumberInput(attrs={'class': 'form-control'}))
    temps_preparation = forms.IntegerField(initial=0, label="Préparation (min)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    temps_cuisson = forms.IntegerField(initial=0, label="Cuisson (min)", widget=forms.NumberInput(attrs={'class': 'form-control'}))
    instructions = forms.CharField(widget=forms.Textarea(attrs={'rows': 3, 'class': 'form-control'}), required=False)
    image = forms.ImageField(required=False, label="Image du plat", widget=forms.ClearableFileInput(attrs={'class': 'form-control'}))
    marge_souhaitee = forms.DecimalField(max_digits=5, decimal_places=2, initial=70.0, required=False, label="Marge souhaitée (%)", widget=forms.NumberInput(attrs={'class': 'form-control'}))

    def save(self, commit=True):
        # This form does not save a single object.
        # The view will handle the creation of PlatMenu and FicheTechnique.
        pass


class CategorieArticleForm(forms.ModelForm):
    class Meta:
        model = CategorieIngredient
        fields = ['nom']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': "Nom de la catégorie"})
        }
        labels = {
            'nom': "Nom de la catégorie d'articles"
        }

class ArticleForm(forms.ModelForm):
    marge = forms.DecimalField(
        max_digits=5, 
        decimal_places=2, 
        required=False, 
        label="Marge (%)",
        help_text="Optionnel. Calcule le prix de vente à partir du CMUP.",
        widget=forms.NumberInput(attrs={
            'class': 'form-control', 
            'placeholder': '0',
            'style': 'max-width: 120px;'
        })
    )

    class Meta:
        model = Ingredient
        fields = ['nom', 'code', 'categorie', 'unite', 'quantite_stock', 'seuil_alerte', 'prix_moyen', 'prix_vente', 'emplacement']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Ex: Tomate, Oignon, etc.'}),
            'code': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Code article'}),
            'categorie': forms.Select(attrs={'class': 'form-control'}),
            'unite': forms.Select(attrs={'class': 'form-control'}),
            'quantite_stock': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Stock initial'}),
            'seuil_alerte': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Seuil d'alerte"}),
            'prix_moyen': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': "Prix d'achat"}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix de vente'}),
            'emplacement': forms.Select(attrs={'class': 'form-control'}),
        }
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['categorie'].queryset = CategorieIngredient.objects.exclude(nom__in=['Boisson', 'Boissons'])


class FournisseurForm(forms.ModelForm):
    class Meta:
        model = Fournisseur
        fields = ['nom', 'personne_contact', 'telephone', 'adresse', 'email']
        widgets = {
            'nom': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Nom du fournisseur'}),
            'personne_contact': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Personne à contacter'}),
            'telephone': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Numéro de téléphone'}),
            'adresse': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Adresse complète'}),
            'email': forms.EmailInput(attrs={'class': 'form-control', 'placeholder': 'adresse@email.com'})
        }

class RecetteForm(forms.ModelForm):
    categorie = forms.ModelChoiceField(
        queryset=CategorieMenu.objects.exclude(nom__in=['Boisson', 'Boissons']),
        label="Catégorie",
        required=True,
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    class Meta:
        model = FicheTechnique
        fields = ['plat', 'nombre_portions', 'temps_preparation', 'temps_cuisson', 'instructions', 'image']
        widgets = {
            'plat': forms.Select(attrs={'class': 'form-control'}),
            'nombre_portions': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Pour combien de personnes ?'}),
            'temps_preparation': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'En minutes'}),
            'temps_cuisson': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'En minutes'}),
            'instructions': forms.Textarea(attrs={'class': 'form-control', 'rows': 5, 'placeholder': 'Instructions de préparation...'}),
            'image': forms.ClearableFileInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Pré-remplir le champ plat et le désactiver s'il est déjà défini
        if self.instance and self.instance.pk and hasattr(self.instance, 'plat'):
            self.fields['plat'].queryset = PlatMenu.objects.filter(pk=self.instance.plat.pk)
            self.fields['plat'].disabled = True
            self.initial['categorie'] = self.instance.plat.categorie
        else:
            # Exclure les plats qui ont déjà une fiche ou qui sont des boissons/accompagnements
            plats_avec_fiche = FicheTechnique.objects.values_list('plat_id', flat=True)
            self.fields['plat'].queryset = PlatMenu.objects.exclude(pk__in=plats_avec_fiche) \
                                                    .exclude(categorie__nom__in=['Boisson', 'Boissons']) \
                                                    .exclude(is_accompagnement=True)

    def save(self, commit=True):
        # La logique de mise à jour du prix du plat est maintenant gérée dans la vue
        # après la sauvegarde du formset pour avoir le coût total du plat.
        return super().save(commit=commit)


class DetailFicheTechniqueForm(forms.ModelForm):
    class Meta:
        model = LigneFicheTechnique
        fields = ['ingredient', 'quantite', 'prix_vente']
        widgets = {
            'ingredient': forms.Select(attrs={'class': 'form-control article-select'}),
            'quantite': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Quantité'}),
            'prix_vente': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Prix de vente'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Exclure les boissons de la sélection d'articles dans une recette
        self.fields['ingredient'].queryset = Ingredient.objects.exclude(categorie__nom__in=['Boisson', 'Boissons', 'Accompagnement', 'Accompagnements'])


DetailFicheTechniqueFormSet = forms.inlineformset_factory(
    FicheTechnique, 
    LigneFicheTechnique, 
    form=DetailFicheTechniqueForm, 
    extra=1, 
    can_delete=True,
    fk_name='fiche'
)
