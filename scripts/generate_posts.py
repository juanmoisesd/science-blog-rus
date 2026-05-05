import json
import os
import re

class PostGenerator:
    """
    Class to generate scientific blog posts following the 'SÍNTESIS EVIDENCIA CIENTÍFICA (PubMed)' protocol.
    """
    def __init__(self, phenomenon, population=None, interest=None):
        self.phenomenon = phenomenon
        self.population = population
        self.interest = interest
        self.search_strategies = []

    def generate_search_strategies(self):
        """Generates 3 PubMed search strategies: Broad, Balanced, and Specific (Step 2)."""
        def get_mesh(term):
            return " ".join([w.capitalize() for w in term.split()])

        broad_terms = f"{self.phenomenon}"
        if self.population:
            broad_terms += f" OR {self.population}"
        broad_query = f"({broad_terms})"

        balanced_query = f'("{get_mesh(self.phenomenon)}"[MeSH Terms] OR "{self.phenomenon}"[All Fields])'
        if self.population:
            balanced_query += f' AND ("{get_mesh(self.population)}"[MeSH Terms] OR "{self.population}"[All Fields])'
        balanced_query += ' AND ("last 5 years"[PDat] AND Humans[Mesh])'

        specific_query = f'("{get_mesh(self.phenomenon)}/*"[MeSH Major Topic])'
        if self.population:
            specific_query += f' AND ("{get_mesh(self.population)}"[MeSH Terms])'
        specific_query += ' AND ("last 5 years"[PDat] AND (Meta-Analysis[Filter] OR Systematic Review[Filter] OR Randomized Controlled Trial[Filter]))'

        self.search_strategies = [
            {"type": "Amplia", "objective": "Máxima sensibilidad", "query": broad_query, "logic": "Términos MeSH amplios + sinónimos; operador OR dominante; sin filtros de diseño"},
            {"type": "Equilibrada", "objective": "Sensibilidad/Precisión óptima", "query": balanced_query, "logic": "MeSH + entry terms; combinación AND/OR; filtros: Humans + últimos 5 лет"},
            {"type": "Específica", "objective": "Máxima precisión", "query": specific_query, "logic": "MeSH específicos + subencabezamientos; operador AND estricto; filtros: últimos 5 лет + Meta-Analysis/Systematic Review/RCT"}
        ]
        return self.search_strategies

    def triage_results(self, raw_input_list):
        """Initial triage: deduplication and exclusion (Step 3A)."""
        seen_identifiers = set()
        cleaned_studies = []
        for study in raw_input_list:
            doi = study.get("doi")
            title = study.get("title")
            identifier = doi or title
            if identifier and identifier in seen_identifiers:
                continue
            if study.get("type", "").lower() in ["editorial", "letter", "abstract de congreso"]:
                continue
            if identifier:
                seen_identifiers.add(identifier)
            cleaned_studies.append(study)
        return cleaned_studies

    def extract_structured_data(self, study_data):
        """Extracts structured data including Risk of Bias (Step 3B & 4)."""
        return {
            "ref": f"📄 [{study_data.get('author', 'Anon')}, {study_data.get('year', 'n.d.')}]",
            "objetivo": study_data.get("objetivo", "Цель не указана"),
            "diseno": study_data.get("diseno", "Не указано"),
            "poblacion": study_data.get("poblacion", "Население не указано"),
            "intervencion": study_data.get("intervencion", "Вмешательство не указано"),
            "hallazgo": study_data.get("hallazgo", "Основной вывод не указан"),
            "limitacion": study_data.get("limitacion", "Критическое ограничение не указано"),
            "nivel": self.evaluate_level(study_data),
            "rob": {
                "seleccion": study_data.get("rob_seleccion", "Неизвестно"),
                "medicion": study_data.get("rob_medicion", "Неизвестно"),
                "confusion": study_data.get("rob_confusion", "Неизвестно"),
                "atricion": study_data.get("rob_atricion", "Неизвестно")
            },
            "n": study_data.get("n", 0)
        }

    def evaluate_level(self, study):
        """Evaluate evidence level (Alta, Media, Baja) (Step 4)."""
        n = study.get("n", 0)
        diseno = study.get("diseno", "").lower()
        is_high_quality_design = any(term in diseno for term in ["rct", "rki", "рки", "meta-анализ", "мета-анализ", "систематический обзор"])
        if n > 100 and is_high_quality_design:
            return "🔴 Высокий (Alta)"
        elif 30 <= n <= 100 or "когорт" in diseno:
            return "🟡 Средний (Media)"
        else:
            return "🟢 Низкий (Baja)"

    def synthesize_evidence(self, structured_studies):
        """Build integrative synthesis model (Step 5) and determine global pattern (Step 6)."""
        high_quality = [s for s in structured_studies if "Высокий" in s["nivel"]]
        medium_quality = [s for s in structured_studies if "Средний" in s["nivel"]]
        low_quality = [s for s in structured_studies if "Низкий" in s["nivel"]]

        if len(high_quality) >= 1 and (len(high_quality) + len(medium_quality)) >= 2:
            pattern = "A"
        elif len(medium_quality) >= 1 or len(high_quality) == 1:
            pattern = "B"
        else:
            pattern = "C"

        consistent = ["Результаты исследований показывают определенную закономерность в изученных переменных."] if pattern != "C" else []

        hierarchy = {
            "solida": "Высокая согласованность + высокое качество" if high_quality else "N/A",
            "probable": "Согласовано, но с методологическими ограничениями" if medium_quality else "N/A",
            "especulacion": "Данные основаны на исследованиях с малым объемом выборки." if low_quality else "N/A"
        }

        guiding_questions = {
            "mediadora": "Какая опосредующая переменная повторяется в нескольких исследованиях?",
            "temporal": "Установлен ли временной порядок (причинно-следственная связь)?",
            "generalizable": "Являются ли результаты обобщаемыми или зависят от контекста?"
        }

        return {
            "mecanismos": consistent,
            "patrones": "Расхождения в результатах коррелируют с различиями в дизайне исследований.",
            "jerarquia": hierarchy,
            "pattern": pattern,
            "guiding_questions": guiding_questions
        }

    def generate_russian_post(self, phenomenon, structured_studies, synthesis):
        """Generates the final blog post in Russian (Step 6)."""
        author = "Хуан Мойсес де ла Серна, доктор психологических наук, магистр нейронаук и биологии поведения, университетский профессор и научный популяризатор"

        post = f"═══════════════════════════════════════\n"
        post += f"СИНТЕЗ: {phenomenon.upper()}\n"
        post += f"═══════════════════════════════════════\n\n"

        post += "### АННОТАЦИЯ\n"
        post += f"Этот отчет представляет собой систематический синтез фактических данных о {phenomenon}. "
        post += "Мы проанализировали последние исследования для предоставления всестороннего обзора.\n\n"

        post += "### 📥 ОБРАБОТКА РЕЗУЛЬТАТОВ\n"
        for s in structured_studies:
            post += f"{s['ref']}\n"
            post += f"├── Цель: {s['objetivo']}\n"
            post += f"├── Дизайн: {s['diseno']}\n"
            post += f"├── Популяция: {s['poblacion']}\n"
            post += f"├── Вмешательство: {s['intervencion']}\n"
            post += f"├── Основной вывод: {s['hallazgo']}\n"
            post += f"├── Критическое ограничение: {s['limitacion']}\n"
            post += f"├── Риск предвзятости:\n"
            post += f"│   ├── Отбор: {s['rob']['seleccion']}\n"
            post += f"│   ├── Измерение: {s['rob']['medicion']}\n"
            post += f"│   ├── Смешение: {s['rob']['confusion']}\n"
            post += f"│   └── Аттриция: {s['rob']['atricion']}\n"
            post += f"└── Уровень доказательности: {s['nivel']}\n\n"

        post += "### 🧠 ИНТЕГРАТИВНЫЙ СИНТЕЗ\n"
        post += "🏗️ СТРУКТУРА СИНТЕЗА\n\n"
        post += "1. СОГЛАСОВАННЫЕ МЕХАНИЗМЫ\n"
        for m in synthesis["mecanismos"]:
            post += f"   └─ {m}\n"
        if not synthesis["mecanismos"]:
            post += "   └─ Нет четко согласованных механизмов.\n"

        post += "\n2. ПРОТИВОРЕЧИВЫЕ ПАТТЕРНЫ\n"
        post += f"   └─ {synthesis['patrones']}\n\n"

        post += "3. ИЕРАРХИЯ ДОСТОВЕРНОСТИ:\n"
        post += f"   ├─ ✅ ТВЕРДЫЕ ДОКАЗАТЕЛЬСТВА: {synthesis['jerarquia']['solida']}\n"
        post += f"   ├─ ⚠️ ВЕРОЯТНАЯ ГИПОТЕЗА: {synthesis['jerarquia']['probable']}\n"
        post += f"   └─ ❓ СПЕКУЛЯЦИЯ: {synthesis['jerarquia']['especulacion']}\n\n"

        post += "❓ КОНТРОЛЬНЫЕ ВОПРОСЫ:\n"
        post += f"- **Переменная-медиатор:** {synthesis['guiding_questions']['mediadora']}\n"
        post += f"- **Временной порядок:** {synthesis['guiding_questions']['temporal']}\n"
        post += f"- **Обобщаемость:** {synthesis['guiding_questions']['generalizable']}\n\n"

        post += "### 🚀 АДАПТИВНЫЙ ВЫВОД\n"
        pattern = synthesis["pattern"]
        if pattern == "A":
            post += "#### (A) СИЛЬНЫЕ ДОКАЗАТЕЛЬСТВА\n"
            post += f"- **Условный каузальный вывод:** {phenomenon} модулируется выявленными переменными.\n"
            post += "- **Импликации:** Клиническое применение оправдано.\n"
        elif pattern == "B":
            post += "#### (B) СРЕДНИЕ ДОКАЗАТЕЛЬСТВА\n"
            post += "- **Провизорная модель:** Предложена модель с известными и неизвестными переменными.\n"
            post += "- **Критически отсутствующие переменные:** Необходимо измерить/контролировать дополнительные параметры.\n"
        else:
            post += "#### (C) СЛАБЫЕ ДОКАЗАТЕЛЬСТВА\n"
            post += "- **Анализ сбоев:** На данном этапе невозможно сделать окончательные выводы.\n"
            post += "- **Карта пробелов:** Необходимы исследования с лучшим контролем переменных.\n"

        post += "\n### ПОДРОБНЫЙ АНАЛИЗ\n"
        post += f"Детальный анализ {phenomenon} показывает сложность взаимодействия различных факторов. "
        post += "Это требует строгого соблюдения методологических стандартов и прозрачности.\n\n"

        post += "### 📚 СПИСОК ЛИТЕРАТУРЫ\n"
        for i, s in enumerate(structured_studies, 1):
            post += f"{i}. {s['ref']}\n"

        post += f"\n### ⚠️ ОГРАНИЧЕНИЯ ЭТОГО СИНТЕЗА\n"
        post += "Анализ ограничен доступными публикациями в PubMed за последние 5 лет.\n\n"
        post += f"Автор: {author}\n"
        return post

if __name__ == "__main__":
    # Internal test/demo functionality
    import sys

    phenomenon_demo = "нейровоспаление"
    generator = PostGenerator(phenomenon_demo)
    generator.generate_search_strategies()

    # Mock studies for verification purposes
    mock_data = [
        {
            "doi": "10.0001/mock.1",
            "author": "Mock Author A",
            "year": "2023",
            "n": 150,
            "objetivo": "Mock Goal",
            "diseno": "РКИ",
            "poblacion": "Mock Population",
            "intervencion": "Mock Intervention",
            "hallazgo": "Mock Finding",
            "limitacion": "Mock Limitation",
            "rob_seleccion": "Низкий",
            "rob_medicion": "Низкий",
            "rob_confusion": "Низкий",
            "rob_atricion": "Низкий"
        }
    ]

    structured = [generator.extract_structured_data(s) for s in mock_data]
    synthesis = generator.synthesize_evidence(structured)
    report = generator.generate_russian_post(phenomenon_demo, structured, synthesis)

    print("PostGenerator initialized and test report generated successfully.")
