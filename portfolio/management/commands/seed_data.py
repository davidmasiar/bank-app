import json
import os
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from portfolio.models import Application, Integration

class Command(BaseCommand):
    help = 'Nacte mockup data z JSON v STRIKTNÍM módu'

    def handle(self, *args, **options):
        json_path = os.path.join(os.getcwd(), 'data.json')
        
        if not os.path.exists(json_path):
            raise CommandError(f'Soubor data.json nenalezen na ceste: {json_path}')

        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)

        # --- KONFIGURACE POVOLENÝCH HODNOT ---
        ALLOWED_CRITICALITY = ['High', 'Medium', 'Low']
        ALLOWED_LIFECYCLE = ['Discovery', 'Active', 'Legacy', 'Decommissioning']
        ALLOWED_SENSITIVITY = ['High', 'Standard', 'Low']
        ALLOWED_INT_TYPES = ['API', 'File', 'Message']
        ALLOWED_DIRECTIONS = ['Inbound', 'Outbound']

        try:
            with transaction.atomic():
                # WIPE starých dat (uvnitř transakce - pokud se import nepovede, data zůstanou)
                self.stdout.write("Zahajuji transakci a čistím stará data...")
                Integration.objects.all().delete()
                Application.objects.all().delete()

                apps_dict = {}
                
                self.stdout.write("Validuji a importuji aplikace...")
                for app_data in data.get('applications', []):
                    name = app_data.get('name')
                    
                    crit = app_data.get('criticality')
                    if crit not in ALLOWED_CRITICALITY:
                        raise ValueError(f"CHYBA: Aplikace '{name}' má neplatnou kritičnost: '{crit}'. Povoleno: {ALLOWED_CRITICALITY}")

                    life = app_data.get('lifecycle_status')
                    if life not in ALLOWED_LIFECYCLE:
                        raise ValueError(f"CHYBA: Aplikace '{name}' má neplatný lifecycle: '{life}'. Povoleno: {ALLOWED_LIFECYCLE}")

                    app = Application.objects.create(
                        name=name,
                        domain=app_data['domain'],
                        is_core=app_data.get('is_core', False),
                        criticality=crit,
                        lifecycle_status=life,
                        business_owner=app_data['business_owner'],
                        it_owner=app_data['it_owner'],
                        vendor=app_data['vendor'],
                        environments=app_data['environments'],
                        region=app_data['region'],
                        hosting=app_data['hosting'],
                        tech_stack=app_data['tech_stack'],
                        database=app_data['database'],
                        runtime=app_data['runtime'],
                        capabilities=app_data['capabilities'],
                        tech_debt=app_data.get('tech_debt', '')
                    )
                    apps_dict[app.name] = app

                self.stdout.write("Validuji a importuji integrace...")
                count_int = 0
                for int_data in data.get('integrations', []):
                    src_name = int_data['source_app_name']
                    trg_name = int_data['target_app_name']
                    
                    source = apps_dict.get(src_name)
                    target = apps_dict.get(trg_name)
                    
                    if not source or not target:
                        missing = src_name if not source else trg_name
                        raise ValueError(f"CHYBA: Integrace odkazuje na neexistující aplikaci: '{missing}'")

                    sens = int_data.get('data_sensitivity')
                    if sens not in ALLOWED_SENSITIVITY:
                        raise ValueError(f"CHYBA: Integrace {src_name} -> {trg_name} má neplatnou citlivost: '{sens}'. Povoleno: {ALLOWED_SENSITIVITY}")

                    i_type = int_data.get('integration_type')
                    if i_type not in ALLOWED_INT_TYPES:
                        raise ValueError(f"CHYBA: Integrace {src_name} -> {trg_name} má neplatný typ: '{i_type}'. Povoleno: {ALLOWED_INT_TYPES}")

                    direction = int_data.get('direction')
                    if direction not in ALLOWED_DIRECTIONS:
                        raise ValueError(f"CHYBA: Integrace {src_name} -> {trg_name} má neplatný směr: '{direction}'. Povoleno: {ALLOWED_DIRECTIONS}")

                    Integration.objects.create(
                        source=source,            
                        target=target,            
                        type=i_type,
                        direction=direction,
                        volume=int_data.get('volume', '0 req/day'),
                        data_sensitivity=sens
                    )
                    count_int += 1
                
                self.stdout.write(self.style.SUCCESS(f'ÚSPĚCH: Naimportováno {len(apps_dict)} aplikací a {count_int} integrací.'))

        except ValueError as e:
            # Zachytí naše validační chyby
            self.stdout.write(self.style.ERROR(str(e)))
            self.stdout.write(self.style.NOTICE("Import byl zrušen. Žádná data v databázi nebyla změněna."))
        except Exception as e:
            # Zachytí nečekané chyby (např. chybějící klíče v JSONu)
            self.stdout.write(self.style.ERROR(f"NEOČEKÁVANÁ CHYBA: {str(e)}"))
            self.stdout.write(self.style.NOTICE("Transakce byla vrácena zpět."))