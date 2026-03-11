from django.core.management.base import BaseCommand
from cuisine.models import Ingredient

class Command(BaseCommand):
    help = 'Fixes the ingredient with PK=10 by setting its emplacement to None'

    def handle(self, *args, **kwargs):
        try:
            ingredient = Ingredient.objects.get(pk=10)
            self.stdout.write(f"Found ingredient: {ingredient.nom}")
            self.stdout.write("Setting emplacement to None...")
            ingredient.emplacement = None
            ingredient.save()
            self.stdout.write(self.style.SUCCESS('Successfully fixed ingredient with PK=10.'))
        except Ingredient.DoesNotExist:
            self.stdout.write(self.style.ERROR('Ingredient with PK=10 not found.'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'An error occurred: {e}'))
