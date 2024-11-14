select assure.num_ref, assure.id_assure, assure.id_bci, 
ks.id_event, Ks.Date_Mammo, 
Ks.Malin_T as pT,
Ks.Malin_N as pN,
if(Ks.Malin_M="1","Mx Inconnues",
if(Ks.Malin_M="2","M0, pas de metastases ou polypectomie par voie naturelle",
if(Ks.Malin_M="3","M1, metastases a distance (dont ganglions sus claviculaire)"," "))) as M,
KS.Taille_MM as Taille_en_mm,
if(Ks.S_Lesloc="509","Sein SAI",
if(Ks.S_Lesloc="508","Lésion étendue du sein",
if(Ks.S_Lesloc="506","Prolongement axillaire",
if(Ks.S_Lesloc="505","QIE",
if(Ks.S_Lesloc="504","QSE",
if(Ks.S_Lesloc="503","QII",
if(Ks.S_Lesloc="502","QSI",
if(Ks.S_Lesloc="501","Région centrale du sein","")))))))) as localisation,
Ks.k_adicap,
Ks.k_adicap2,
Ks.Grade as Grade_SBR,
if(Ks.K_Proges="O" and ks.RH="+","Positif",if(Ks.K_Proges="O" and ks.RH="-","Négatif"," ")) as RH_Progesterone,
if(Ks.K_Oestro="O" and ks.RH="+","Positif",if(Ks.K_Oestro="O" and ks.RH="-","Négatif"," ")) as RH_Oestreogene,
Ks.HER2,
if(Ks.Malin_Type="1","In Situ Canalaire",
if(Ks.Malin_Type="2","In Situ Lobulaire",
if(Ks.Malin_Type="3","Invasif",
if(Ks.Malin_Type="6","Micro-invasif"," ")))) as Si_Malin,
if(Ks.Benin_Type="1","Fibroadénome",
if(Ks.Benin_Type="2","Kyste solitaire",
if(Ks.Benin_Type="3","Adénose Sclérosante",
if(Ks.Benin_Type="4","Galactophorite-Ectasie",
if(Ks.Benin_Type="5","papillome",
if(Ks.Benin_Type="6","Dystrophie-Mastose fibrokystique",
if(Ks.Benin_Type="7","Prolifération épithéliale",
if(Ks.Benin_Type="8","Paget"," ")))))))) as Si_Benin,
if(Ks.Situation_Finale="K","KS_confirmé"," ") as KS_Confirme,
Ks.Date_Bilan as Date_Anapath,
Ks.Date_Inter as Date_Inter_Chir,
Ks.Trait_Radi,
Ks.Date_Radi,
Ks.Trait_Horm,
Ks.Date_Horm,
Ks.Trait_Chim,
Ks.Date_Chim

from assure join ks using (id_assure)
where ks.date_mammo between "date1" and "date2"