# BoardGameServerSimple


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

## Bilder
![Brett for en spiller](https://github.com/kaifriis/BoardGameServerSimple/blob/master/regler.jpg)
![Regler for de ulike fasene for en spiller](https://github.com/kaifriis/BoardGameServerSimple/blob/master/spill.jpg)


## Din klient

Først må du registrere spilleren din. endepunktet /
Du skal skrive en klient som spiller spillet. Endepunktet %TODO% gir deg spillets
tilstad. Du ser at det er din tur når "CurrentPlayer" har 
