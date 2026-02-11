import json
from django.shortcuts import render, redirect, get_object_or_404
from django.db.models import Count
from .models import Application, Integration
from .forms import IntegrationForm
from .utils import ask_llm
from django.db.models import Q
import json
import re


def dashboard(request):
    total_apps = Application.objects.count()
    total_integrations = Integration.objects.count()
    
    # Seřadíme podle počtu, aby grafy dávaly smysl
    criticality_stats = Application.objects.values('criticality').annotate(count=Count('id')).order_by('-count')
    domain_stats = Application.objects.values('domain').annotate(count=Count('id')).order_by('-count')

    return render(request, 'portfolio/dashboard.html', {
        'total_apps': total_apps,
        'total_integrations': total_integrations,
        'criticality_stats': criticality_stats,
        'domain_stats': domain_stats,
    })

def app_list(request):
    search_query = request.GET.get('q', '')
    domain_filter = request.GET.get('domain', '')
    criticality_filter = request.GET.get('criticality', '')
    region_filter = request.GET.get('region', '')

    apps = Application.objects.all()

    if search_query:
        apps = apps.filter(
            Q(name__icontains=search_query) |
            Q(tech_stack__icontains=search_query) |
            Q(vendor__icontains=search_query) |
            Q(database__icontains=search_query)
        )

    if domain_filter:
        apps = apps.filter(domain=domain_filter)
    
    if criticality_filter:
        apps = apps.filter(criticality=criticality_filter)
        
    if region_filter:
        apps = apps.filter(region=region_filter)

    # Získání unikátních hodnot pro dropdown menu ve filtru
    domains = Application.objects.values_list('domain', flat=True).distinct().order_by('domain')
    criticalities = Application.objects.values_list('criticality', flat=True).distinct()
    regions = Application.objects.values_list('region', flat=True).distinct()

    context = {
        'apps': apps,
        'domains': domains,
        'criticalities': criticalities,
        'regions': regions,
        'search_query': search_query,
    }
    return render(request, 'portfolio/app_list.html', context)

def app_detail(request, pk):
    app = get_object_or_404(Application, pk=pk)
    integrations = Integration.objects.filter(source=app) | Integration.objects.filter(target=app)
    return render(request, 'portfolio/app_detail.html', {'app': app, 'integrations': integrations})


def generate_mermaid(request, pk):
    app = get_object_or_404(Application, pk=pk)
    # Načteme okolí aplikace (max 15 integrací)
    integrations = Integration.objects.filter(Q(source=app) | Q(target=app))[:15]
    
    lines = []
    for i in integrations:
        src_id = i.source.name.replace(" ", "_")
        tgt_id = i.target.name.replace(" ", "_")
        lines.append(f'{src_id}("{i.source.name}") -- {i.type} --> {tgt_id}("{i.target.name}")')
    
    ctx = "\n".join(lines)
    main_app_id = app.name.replace(" ", "_")

    prompt_generate = f"""
    Vytvoř Mermaid.js flowchart (graph TD) pro aplikaci {app.name}.
    
    DATA INTEGRACÍ:
    {ctx}
    
    INSTRUKCE:
    1. Hlavní aplikaci '{main_app_id}' zvýrazni stylem (style {main_app_id} fill:#f9f,stroke:#333,stroke-width:4px).
    2. Vrať POUZE kód grafu. Začni s 'graph TD'.
    3. Nepoužívej markdown bloky.
    """
    
    raw_code = ask_llm(prompt_generate)
    
    if raw_code.startswith("ERROR_"):
        return render(request, 'portfolio/partials/mermaid_error.html', {
            'error_msg': "Diagram nelze generovat: Chybí nebo je neplatný API klíč."
        })

    def clean_mermaid(text):
        text = re.sub(r'```mermaid|```', '', text).strip()
        if "graph " in text:
            return text[text.find("graph "):]
        return text

    current_code = clean_mermaid(raw_code)

    prompt_validate = f"""
    Zkontroluj tento Mermaid kód na syntaktické chyby.
    
    KÓD:
    {current_code}
    
    ÚKOL:
    Odpověz POUZE ve formátu JSON:
    {{
        "is_valid": true/false,
        "error_description": "Popis chyby nebo null"
    }}
    """
    
    validation_response = ask_llm(prompt_validate)
    
    if validation_response.startswith("ERROR_"):
        return render(request, 'portfolio/partials/mermaid_content.html', {'mermaid_code': current_code})

    try:
        val_json = json.loads(re.sub(r'```json|```', '', validation_response).strip())
        is_valid = val_json.get("is_valid", False)
        error_msg = val_json.get("error_description", "Unknown error")
    except:
        is_valid = False
        error_msg = "Validation output parsing failed"

    if not is_valid:
        prompt_fix = f"""
        Oprav následující Mermaid kód.
        
        CHYBA: {error_msg}
        
        ŠPATNÝ KÓD:
        {current_code}
        
        INSTRUKCE:
        Vrať POUZE opravený kód (graph TD...). Žádný text okolo.
        """
        fixed_code = ask_llm(prompt_fix)
        
        if not fixed_code.startswith("ERROR_"):
            current_code = clean_mermaid(fixed_code)

    return render(request, 'portfolio/partials/mermaid_content.html', {'mermaid_code': current_code})
    
def qa_view(request):
    if 'chat_history' not in request.session:
        request.session['chat_history'] = []
    
    if request.method == "POST":
        # 1. Získání a vyčištění dotazu (Pojistka z verze 2)
        question = request.POST.get('question', '').strip()
        
        # 2. Kontrola prázdného dotazu
        if not question:
            if request.headers.get('HX-Request'):
                return HttpResponse('<div class="flex justify-start animate-fade-in"><div class="bg-gray-100 text-gray-400 p-3 rounded-2xl text-[10px] font-black uppercase">⚠️ Musíte vyplnit dotaz</div></div>')
            return redirect('qa_view')

        # 3. Sběr detailních dat o aplikacích (Grounding z verze 1)
        apps = Application.objects.all()[:40]
        app_list = [
            f"{a.name}: Doména={a.domain}, Kritičnost={a.criticality}, Dluh={a.tech_debt}, "
            f"Integrace={Integration.objects.filter(Q(source=a) | Q(target=a)).count()}" 
            for a in apps
        ]
        context_data = "\n".join(app_list)
        
        # 4. Ten tvůj vyladěný prompt pro Senior Architekta (z verze 1)
        full_prompt = (
            "Jsi Senior IT Architekt v Raiffeisenbank. Odpovídej VŽDY A POUZE ČESKY. "
            f"ZDE JSOU AKTUÁLNÍ DATA PORTFOLIA: \n{context_data}\n\n"
            "TVOJE STRIKTNÍ PRAVIDLA ODPOVĚDI:\n"
            "1. JAZYK: Celá tvoje odpověď musí být v češtině. Nepoužívej anglické věty.\n"
            "2. FORMÁT: Piš jako jeden souvislý odstavec textu. Nepoužívej žádné seznamy ani odrážky.\n"
            "3. ZÁKAZ MARKDOWNU: Je přísně zakázáno používat hvězdičky (**), mřížky (#), tabulky nebo tučné písmo.\n"
            "4. DÉLKA: Buď stručný a profesionální, maximálně 2 až 3 věty.\n"
            "5. LOGIKA: Kritičnost 'High' znamená, že aplikaci nelze vyřadit. Kandidátem na vyřazení je jen Low/Medium s vysokým dluhem.\n"
            "6. OCHRANA: Pokud se dotaz netýká banky nebo tohoto portfolia, odpověz česky, že se specializuješ jen na IT architekturu.\n\n"
            f"DOTAZ UŽIVATELE: {question}"
        )
        
        # 5. Volání LLM
        answer = ask_llm(full_prompt)

        # 6. Kontrola chybových stavů API (Pojistka z verze 2)
        if answer.startswith("ERROR_"):
            error_text = "V systému chybí API klíč pro OpenAI."
            if answer == "ERROR_INVALID_KEY":
                error_text = "API klíč je neplatný nebo vypršel."
            elif "TIMEOUT" in answer:
                error_text = "AI trvalo generování příliš dlouho. Zkuste to znovu."

            if request.headers.get('HX-Request'):
                return render(request, 'portfolio/partials/chat_error.html', {'error_msg': error_text})
            return render(request, 'portfolio/qa.html', {'error': error_text, 'chat_history': request.session['chat_history']})

        # 7. Čištění odpovědi od Markdownu (z verze 1)
        clean_answer = answer.replace("**", "").replace("#", "").replace("__", "").replace("|", "").strip()
        
        # 8. Uložení do historie v session
        request.session['chat_history'].append({'user': question, 'ai': clean_answer})
        request.session.modified = True 

        # 9. HTMX vs Klasický render
        if request.headers.get('HX-Request'):
            return render(request, 'portfolio/partials/chat_message.html', {
                'user_msg': question, 
                'ai_msg': clean_answer
            })
            
    return render(request, 'portfolio/qa.html', {'chat_history': request.session['chat_history']})

def clear_chat(request):
    if 'chat_history' in request.session:
        del request.session['chat_history']
    return redirect('qa_view')

def global_analysis(request):
    apps = Application.objects.all()
    app_data = []
    for app in apps:
        info = (
            f"ID:{app.id} | Name:{app.name} | Domain:{app.domain} | "
            f"Crit:{app.criticality} | Status:{app.lifecycle_status} | "
            f"Stack:{app.tech_stack} | Debt:{app.tech_debt}"
        )
        app_data.append(info)
    
    context_data = "\n".join(app_data)

    prompt = f"""
    Jsi Senior IT Architekt. Analyzuj portfolio a vrať POUZE validní JSON objekt.
    Nesmíš psát žádný úvodní text, jen čistý JSON.
    
    DATA PORTFOLIA:
    {context_data}

    POŽADOVANÁ STRUKTURA JSON:
    {{
        "summary": "Manažerské shrnutí stavu portfolia (max 2-3 věty, česky).",
        "top_refactoring": [
            {{ 
                "name": "Název aplikace", 
                "criticality": "Kritičnost", 
                "reason": "Konkrétní důvod pro refaktoring (např. vysoký dluh + high critical)",
                "priority": 1 
            }}
            // Zde vypiš přesně 5 nejdůležitějších kandidátů (seřazeno 1-5)
        ],
        "main_risks": [
            "Popis rizika 1 (např. závislost na legacy DB)",
            "Popis rizika 2 (např. EOL technologie)"
            // Uveď 3 až 5 hlavních rizik
        ],
        "tech_debt_areas": [
            {{ "area": "Oblast (např. Java verze, Oracle)", "count": "Odhad počtu zasažených apps", "impact": "Vysoký/Střední" }}
        ]
    }}
    """

    raw_response = ask_llm(prompt)

    try:
        clean_json = re.sub(r'```json\s*|\s*```', '', raw_response).strip()
        
        start = clean_json.find('{')
        end = clean_json.rfind('}') + 1
        if start != -1 and end != 0:
            clean_json = clean_json[start:end]
            
        analysis_data = json.loads(clean_json)
    except Exception as e:
        print(f"Chyba parsování JSON: {e}")
        analysis_data = {
            "error": True,
            "raw": raw_response
        }

    return render(request, 'portfolio/analysis.html', {'analysis': analysis_data})

def integration_list(request):
    return render(request, 'portfolio/integration_list.html', {'integrations': Integration.objects.all()})

def integration_create(request):
    form = IntegrationForm(request.POST or None)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('integration_list')
    return render(request, 'portfolio/integration_form.html', {'form': form, 'title': 'Nová integrace'})

def integration_update(request, pk):
    obj = get_object_or_404(Integration, pk=pk)
    form = IntegrationForm(request.POST or None, instance=obj)
    if request.method == 'POST' and form.is_valid():
        form.save()
        return redirect('integration_list')
    return render(request, 'portfolio/integration_form.html', {'form': form, 'title': 'Upravit integraci'})

def integration_delete(request, pk):
    obj = get_object_or_404(Integration, pk=pk)
    if request.method == 'POST':
        obj.delete()
        return redirect('integration_list')
    return render(request, 'portfolio/integration_confirm_delete.html', {'integration': obj})
    
def clear_chat(request):
    if 'chat_history' in request.session:
        del request.session['chat_history']
    return redirect('qa_view')