# BRANCH 3 : Application (Streamlit Web App)
# Responsable : Romain Lesueur

import streamlit as st
import pandas as pd
import numpy as np
import joblib
import os

st.set_page_config(page_title="Simulateur de Crédit", layout="wide")

def main():
    st.title("Simulateur de Crédit Bancaire")
    st.markdown("Remplissez le formulaire ci-dessous pour évaluer l'éligibilité d'un nouveau client.")

    @st.cache_resource
    def load_model():
        path_model = 'best_model_xgb_small.pkl'
        path_features = 'model_features_small.pkl'
        
        if not os.path.exists(path_model) or not os.path.exists(path_features):
            st.error("Erreur : Modèle ou liste des features introuvable. Veuillez exécuter modeling.ipynb.")
            return None, None
            
        model = joblib.load(path_model)
        features = joblib.load(path_features)
        return model, features

    model, features = load_model()

    if model is None:
        return

    with st.form("credit_form"):
        st.subheader("Informations Client")
        
        col1, col2, col3 = st.columns(3)
        
        input_data = {}
        
        with col1:
            st.markdown("### Scores & Documents")
            # Variables externes (souvent les plus importantes)
            input_data['EXT_SOURCE_2'] = st.number_input("Score Externe 2 (0.0 - 1.0)", min_value=0.0, max_value=1.0, value=0.5)
            input_data['EXT_SOURCE_3'] = st.number_input("Score Externe 3 (0.0 - 1.0)", min_value=0.0, max_value=1.0, value=0.5)
            input_data['EXT_SOURCE_1'] = st.number_input("Score Externe 1 (0.0 - 1.0)", min_value=0.0, max_value=1.0, value=0.5)
            
            doc_3 = st.checkbox("Document 3 fourni ?", value=True)
            input_data['FLAG_DOCUMENT_3'] = 1 if doc_3 else 0

        with col2:
            st.markdown("### Profil Personnel")
            # Genre
            gender = st.radio("Genre", ["Homme", "Femme"])
            input_data['CODE_GENDER_M'] = 1 if gender == "Homme" else 0
            input_data['CODE_GENDER_F'] = 1 if gender == "Femme" else 0
            
            # Education
            education = st.selectbox("Niveau d'éducation", ["Enseignement Supérieur", "Secondaire / Spécial", "Autre"])
            input_data['NAME_EDUCATION_TYPE_Higher education'] = 1 if education == "Enseignement Supérieur" else 0
            input_data['NAME_EDUCATION_TYPE_Secondary / secondary special'] = 1 if education == "Secondaire / Spécial" else 0
            
            # Revenu
            income_type = st.selectbox("Type de revenu", ["Travailleur", "Retraité", "Autre"])
            input_data['NAME_INCOME_TYPE_Working'] = 1 if income_type == "Travailleur" else 0
            input_data['NAME_INCOME_TYPE_Pensioner'] = 1 if income_type == "Retraité" else 0

        with col3:
            st.markdown("### Historique & Contrat")
            # Contrat
            contract = st.radio("Type de Prêt", ["Prêt Espèces (Cash Loan)", "Crédit Renouvelable"])
            input_data['NAME_CONTRACT_TYPE_Cash loans'] = 1 if contract == "Prêt Espèces (Cash Loan)" else 0
            
            # Historique Crédit / Carte
            input_data['cc_CNT_DRAWINGS_ATM_CURRENT_mean'] = st.number_input("Moy. Retraits ATM (Carte)", value=0.0)
            input_data['cc_CNT_DRAWINGS_CURRENT_mean'] = st.number_input("Moy. Retraits Totaux (Carte)", value=0.0)
            input_data['prev_CNT_PAYMENT_max'] = st.number_input("Max échéances préc.", value=12.0)
            input_data['pos_SK_DPD_DEF_mean'] = st.number_input("Moy. Jours Retard (POS)", value=0.0)

        submitted = st.form_submit_button("Lancer la Prédiction")

    if submitted:
        # Préparation du DataFrame pour la prédiction
        # On initialise avec des zéros
        df_input = pd.DataFrame(columns=features)
        df_input.loc[0] = 0 
        
        # On remplit avec les valeurs saisies si la colonne existe
        for col, val in input_data.items():
            if col in features:
                df_input.at[0, col] = val
            
        # Gestion des variables manquantes dans le formulaire mais présentes dans le modèle
        # (Au cas où le top 15 change légèrement à chaque entraînement)
        # On affiche un warning si des variables importantes manquent
        missing_cols = [col for col in features if col not in input_data]
        if missing_cols:
             with st.expander("Détails techniques (Variables manquantes mises à 0)"):
                st.write(missing_cols)

        # Prédiction
        proba = model.predict_proba(df_input)[0][1]
        seuil = 0.5
        prediction = 1 if proba > seuil else 0

        st.divider()
        st.subheader("Résultat de la simulation")
        
        c1, c2 = st.columns([1, 2])
        
        with c1:
            st.metric(label="Probabilité de Défaut", value=f"{proba:.1%}")
            
            if prediction == 1:
                st.error("CRÉDIT REFUSÉ (Risque Élevé)")
            else:
                st.success("CRÉDIT ACCEPTÉ (Risque Faible)")
                
        with c2:
            st.progress(float(proba))
            st.caption("0% (Sûr) ---------------------------------------- 100% (Risqué)")

if __name__ == "__main__":
    main()