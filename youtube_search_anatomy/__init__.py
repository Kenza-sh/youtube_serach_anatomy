import logging
from youtube_search import YoutubeSearch
from gliner import GLiNER
import re

class AnatomieVideoSearch:
    def __init__(self):
        self.model = GLiNER.from_pretrained("almanach/camembert-bio-gliner-v0.1")
        self.labels = ["Examen Médical", "Anatomie", "Maladie", "Symptôme", 'Signe','Traitement',
                       'Médicament','État Physiologique','Facteur de Risque','Pathogène',
                       'Unité de Mesure','terme médical']
        self.chaines_valides = ["Anat' Academy", "Carl Gdt (Anat' To Me)", "Docteur Par Coeur",
                                "Dr Explique", "scandium theory", "Docteur C", "Promed Anatomie (Dr Khaled ANNABI)",
                                "RB Physio", "Anatomie 3D Lyon", "Urologie fonctionnelle - Anatomie",
                                "Encyclopédie Médicale", "Médecine Créative","Physio explain","Anatomyc"]
        
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
        logging.info("Modèle GLiNER chargé avec succès.")

    def get_entities(self, text):
        """Extrait les entités de type 'Anatomie' d'un texte donné."""
        try:
            logging.info("Extraction des entités d'anatomie en cours...")
            text = text.lower()
            liste_anatomie = []
            entities = self.model.predict_entities(text, self.labels, threshold=0.2, flat_ner=True)
            for entity in entities:
                if entity["label"] == 'Anatomie':
                    liste_anatomie.append(entity["text"])
            logging.info(f"Entités extraites : {liste_anatomie}")
            return list(set(liste_anatomie))
        except Exception as e:
            logging.error(f"Erreur lors de l'extraction des entités : {e}")
            return []

    def recherche_video(self, entities):
        """Recherche des vidéos YouTube en fonction des entités anatomiques extraites."""
        filtered_results = []
        print(entities)
        try:
            for entité in entities:
                logging.info(f"Recherche de vidéos pour l'entité : {entité}")
                results = YoutubeSearch(f"anatomie du {entité}", max_results=200).to_dict()
                pattern = re.compile(rf"\b{re.escape(entité)}\b", re.IGNORECASE)
                for result in results:
                    title = result["title"].lower()
                    if any(chaine.lower() in result["channel"].lower() for chaine in self.chaines_valides):
                        video_url = f"https://www.youtube.com{result['url_suffix']}"
                        duration = result.get('duration', '0')
                        res = duration.split(":")
                        total_seconds = sum(int(x) * (60 ** i) for i, x in enumerate(reversed(res)))
                        if total_seconds < 300 or pattern.search(title):
                            filtered_results.append(video_url)
                            break
            logging.info(f"Vidéos trouvées : {filtered_results}")
            return list(set(filtered_results))
        except Exception as e:
            logging.error(f"Erreur lors de la recherche des vidéos : {e}")
            return []


searcher = AnatomieVideoSearch()
def main(req: func.HttpRequest) -> func.HttpResponse:
    logging.info('Python HTTP trigger function processed a request.')

    try:
        req_body = req.get_json()
        query = req_body.get('text')

        if not query:
            return func.HttpResponse(
                json.dumps({"error": "No query provided in request body"}),
                mimetype="application/json",
                status_code=400
            )
        
        entites = searcher.get_entities(query)
        videos = searcher.recherche_video(entites)

        return func.HttpResponse(
            json.dumps({"response": videos}),
            mimetype="application/json"
        )

    except Exception as e:
        logging.error(f"Error processing request: {str(e)}")
        return func.HttpResponse(
            json.dumps({"error": str(e)}),
            mimetype="application/json",
            status_code=500
        )
