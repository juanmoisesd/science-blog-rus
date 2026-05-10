from generate_posts import PostGenerator
import os

def test_synthesis():
    phenomenon = "нейровоспаление при депрессии"
    generator = PostGenerator(phenomenon)

    # Scenario A: Strong Evidence
    strong_studies = [
        {
            "doi": "10.1001/example.a1",
            "author": "Ivanov et al.",
            "year": "2023",
            "n": 200,
            "objetivo": "Оценить влияние цитокинов",
            "diseno": "РКИ",
            "poblacion": "200 взрослых",
            "intervencion": "Антагонисты IL-6",
            "hallazgo": "Улучшение состояния",
            "limitacion": "Краткосрочность",
            "rob_seleccion": "Низкий",
            "rob_medicion": "Низкий",
            "rob_confusion": "Низкий",
            "rob_atricion": "Низкий"
        },
        {
            "doi": "10.1016/example.a2",
            "author": "Petrov et al.",
            "year": "2022",
            "n": 120,
            "objetivo": "Мета-анализ маркеров",
            "diseno": "Мета-анализ",
            "poblacion": "800 пациентов",
            "intervencion": "Систематический обзор",
            "hallazgo": "Повышение СРБ",
            "limitacion": "Гетерогенность",
            "rob_seleccion": "Низкий",
            "rob_medicion": "Низкий",
            "rob_confusion": "Низкий",
            "rob_atricion": "Средний"
        }
    ]
    structured_a = [generator.extract_structured_data(s) for s in strong_studies]
    synthesis_a = generator.synthesize_evidence(structured_a)
    assert synthesis_a["pattern"] == "A"

    post_a = generator.generate_russian_post(phenomenon, structured_a, synthesis_a)
    assert "СИЛЬНЫЕ ДОКАЗАТЕЛЬСТВА" in post_a
    assert "Риск предвзятости" in post_a
    assert "КОНТРОЛЬНЫЕ ВОПРОСЫ" in post_a

    # Scenario C: Weak Evidence
    weak_studies = [
        {
            "doi": "10.1111/example.c1",
            "author": "Sidorov et al.",
            "year": "2021",
            "n": 15,
            "objetivo": "Пилот",
            "diseno": "Поперечное",
            "poblacion": "15 человек",
            "intervencion": "Наблюдение",
            "hallazgo": "Слабая корреляция",
            "limitacion": "N",
            "rob_seleccion": "Высокий",
            "rob_medicion": "Средний",
            "rob_confusion": "Высокий",
            "rob_atricion": "Низкий"
        }
    ]
    structured_c = [generator.extract_structured_data(s) for s in weak_studies]
    synthesis_c = generator.synthesize_evidence(structured_c)
    assert synthesis_c["pattern"] == "C"

    post_c = generator.generate_russian_post(phenomenon, structured_c, synthesis_c)
    assert "СЛАБЫЕ ДОКАЗАТЕЛЬСТВА" in post_c

    print("All functional tests passed!")

if __name__ == "__main__":
    test_synthesis()
