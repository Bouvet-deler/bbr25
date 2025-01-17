# BoardGameServerSimple

## Starte serveren

1. Last ned .NET SDK 9
2. Gå til undermappa BoardGameServerSimple
3. Kjør `dotnet run`. Serveren vil bygges og printe hvilken port den lytter på.
4. Gå til `http://**server address**/scalar/v1` for å se OpenAPI-docs

## Spillet


Du kan hente spilltilstanden på endepunktet /api/game

Det er tre felter som avgjør hva slags handlinger du skal gjøre. 

Det er CurrentState, CurrentPhase, og current player.

Så lenge du har kort i TradedCards, 
Spillet starter med CurrentState = "Registering".
Da kan du registrere klienten din som en spiller i spillet, med endepunktet
api/game/join

**Merk:** Hvis du får Bad request på denne kan det hende at noen andre har registrert en spiller med samme navn. Sjekk feilmelding. 

Når har gjort det, må du vente på at tilstanden i CurrentState blir "Playing", og at
CurrentPlayer gir navnet du registrerte med join. 
Du vil få tilbake en guid som identifiserer spilleren din. Denne må du lagre for videre
bruk.

Når CurrentState er Playing og CurrentPlayer er din spiller, er det din tur til å
spille.

Da er det CurrentPhase som bestemmer hvilke handlinger som er lovlige.
En tur starter med Fasen "Planting". Da MÅ du plante det første kortet i hånden din. 
Dette gjør du med endepunktet 
/api/playing/plant. 
Du må oppgi spillerguiden for å autentisere deg, og feltet du vil plante kortet i. Du
trenger ikke oppgi kortet du vil plante, da du bare har lov til å plante ett kort.

Neste fase er da PlantingOptional. Her kan du plante et kort til om du vil, og da bruker
du samme endepunkt som i Planting igjen.
Du kan også velge å avslutte planting, ved å kalle endepunktet
/api/playing/end-planting,
som tar oss videre til byttefasen. 

Fasen blir satt til Trading, og spille trekker to kort for deg som aktiv
spilleren(CurrentPlayer), som ligger i DrawnCards. For å se dine nye kort må klienten 
pulle state fra spillserveren.

Her kan alle spillere bli med å bytte, men de må bytte med den aktive spilleren. 

Når du er ferdig med trading, kan du velge å avslutte Trading med endepunktet
api/playing/end-trading

Da er fasen "TradePlanting".
Nå MÅ du plante alle kortene du har byttet til deg, enten du er aktiv spiller eller ikke

endepunktet er /api/playing/trade-plant

Dette endepunktet fungerer som plant -endepunktet, bortsett fra at du må gi hvilket kort
du skal plante. dette er fordi du kan plante dem i den rekkefølgen du vil.

Når alle har plantet sine kort, blir det neste spillers tur.



|--------------------------|Planting|PlantingOptional|Trading|Tradeplanting|
|--------------------------|--------|----------------|-------|-------------|
|/api/playing/plant        |       x|               x|       |             |
|/api/playing/end-planting |        |               x|       |             |
|                          |        |                |       |             |
|/api/playing/end-trading  |        |                |      x|             |
|/api/playing/trade-plant  |        |                |       |            x|
|/api/playing/harvest-field|       x|              x |      x|            x|


|--------------------------|Du er aktiv spiller|Du er ikke aktiv spiller|
|--------------------------|-------------------|------------------------|
|/api/playing/plant        |                  x|                        |
|/api/playing/end-planting |                  x|                        |
|                          |                   |                        |
|/api/playing/end-trading  |                  x|                        |
|/api/playing/trade-plant  |                  x|                       x|
|/api/playing/harvest-field|                  x|                       x|


## Regler (og validering)
Her er en oversikt over reglene i spillet. Det er lagt ved en feilkode, som blir 

Spillregel 1: Du skal kun ha en type bønne plantet i hvert field

Spillregel 2: Du må plante det første kortet du har på hånda

Spillregel 3: Du kan velge å plante et kort til om du vil. om du ikke vil det, må du kalle endepunktet

for å avslutte planting

Spillregel 4: om du må plante et kort som du ikke har plass til, må du høste en åker
har du ikke kort på hånden, går du rett til fase 2


Regler for bønnebytting

Spillregel 5: Bønner kan ikke byttes mellom to spillere som ikke er aktive.

Spillregel 6: Du kan bytte vekk håndkort uansett hvor i rekkefølgen du har dem på hånda

Spillregel 7: Den aktive spilleren kan bytte bort både håndkort og kortene den har trukket fra
trekkebunken

Spillregel 8: du kan ikke bytte bort kort som allerede er byttet

Spillregel 9: du kan ikke bytte bort allerede plantede kort

Spillregel 10: du kan bytte et hvilket som helst antall bønner mot et hvilket som helst antall bønner

Spillregel 11: bønnebyttet er ikke over før den aktive spilleren kaller endepunktet for å avslutte
bønnebytting

Regler for trade-planting
Spillregel 12: Alle som har byttet til seg kort må nå plante dem. Om aktiv spiller har avdekket kort
som ikke er byttet bort (DrawnCards) så må de også plantes

Spillregel 13: Når alle har plantet sine kort trekker den aktive spilleren 3 kort, og turen går videre
til neste spiller, som skal plante

Spillregel 14: Regelen til bønnenes beskyttelse. Du har ikke lov til å høste en pker med bare
en bønne om du har andre åkere med 2 eller flere

Tekniske regeler:

Teknisk regel 1: Spillet må være i gang for at du skal kunne gjøre handlinger

Teknisk regel 2: Du kan bare spille når det er din tur

Teknisk regel 3: du kan bare utføre en handling du er i den fasen handlingen hører til
Teknisk regel 4: Du kan kun plante i felt som eksisterer
## Offisielle regler: 
Merk reglene i det offisielle spillet for forhandlinger er noe forskjellig i denne versjon. Her er det hele tiden er gjeldende spiller som foreslår bytter de andre kan godta eller avstå fra. Andre spillere kan ikke foreslå andre bytter. (Feel free to implement.)
[Offisielle Bohnanza regler (PDF)](https://www.riograndegames.com/wp-content/uploads/2013/02/Bohnanza-Rules.pdf)

## Bilder
![Brett for en spiller](https://github.com/Bouvet-deler/bbr25/blob/master/regler.jpg)
![Regler for de ulike fasene for en spiller](https://github.com/Bouvet-deler/bbr25/blob/master/spill.jpg)


## Din klient
Open API dokumentasjon for spillserver finner du her: 
https://**server address**/scalar/v1

Først må du registrere spilleren din. endepunktet /
Du skal skrive en klient som spiller spillet. Endepunktet %TODO% gir deg spillets
tilstad. Du ser at det er din tur når "CurrentPlayer" har 
