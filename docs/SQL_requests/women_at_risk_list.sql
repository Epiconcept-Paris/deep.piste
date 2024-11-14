select assure.num_ref, assure.id_assure, assure.id_bci,
ks.id_event, Ks.Date_Mammo,
(datediff(Ks.Date_mammo,Assure.Date_Naiss)/365.25) as Age_Mammo,

if(Ks.Menop_Trai="O","Oui","Non") as THS,
if(Ks.Maladie_an_d="k" or Ks.Maladie_an_G="k","Oui","Non") as ATCD_Cancer,
if(Ks.Maladie_an_d="k" or Ks.Maladie_an_G="k",datediff(Ks.Operation_Date,Assure.Date_Naiss)/365.25," ") as Age_ATCD_Cancer,
if(Ks.Maladie_an_d="k" and Ks.Maladie_an_G="k","Oui","Non") as ATCD_Cancer_Bilateral,
if(Ks.Maladie_an_d="k" and Ks.Maladie_an_G="k",datediff(Ks.Operation_Date,Assure.Date_Naiss)/365.25," ") as Age_ATCD_Cancer_Bilateral,
if(Ks.Maladie_an_d="E" or Ks.Maladie_an_G="E","Oui","Non") as ATCD_Chir_Esth,
if(Ks.Maladie_an_d="E" or Ks.Maladie_an_G="E",datediff(Ks.Operation_Date,Assure.Date_Naiss)/365.25," ") as Age_ATCD_Chir_Esth,
if(Ks.Ant_Age_Mere="O","O","N") as ATCD_Famil_Mere,
if(Ks.Ant_Age_Mere="O",KS.Age_Mere," ") as Age_ATCD_Famil_Mere,
if(Ks.Ant_Age_soeur="O","O","N") as ATCD_Famil_Soeur,
if(Ks.Ant_Age_soeur="O",Ks.Age_Soeur," ") as Age_ATCD_Famil_Soeur,
if(Ks.Ant_Age_fille="O","O","N") as ATCD_Famil_Fille,
if(Ks.Ant_Age_fille="O",Ks.Age_fille," ") as Age_ATCD_Famil_Fille,
if(Ks.Ant_Age_autre="O","O","N") as ATCD_Famil_Autre,
if(Ks.Ant_Age_autre="O",Ks.Age_autre," ") as Age_ATCD_Famil_Autre

from assure join ks using (id_assure)
where ks.date_mammo between "date1" and "date2"