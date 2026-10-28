# BoutiquePilot — Accueil premium

BoutiquePilot est désormais un MVP multi-commerçants : chaque utilisateur peut s’inscrire, se connecter et gérer sa propre boutique, séparée de celles des autres comptes.

## Essayer maintenant

Utilisez l’**aperçu en direct « BoutiquePilot — Titre animé »**. Le fichier HTML seul ne suffit plus : inscription, connexion et enregistrement ont besoin du serveur.

1. Sur la page d’accueil publique, cliquez sur **Commencer** ou **Créer mon espace boutique**. Dans **Créer mon compte**, renseignez votre nom, le nom de votre boutique, votre e-mail et un mot de passe unique d’au moins 10 caractères.
2. Après inscription, votre espace s’ouvre avec une boutique vide, sans données fictives.
3. Ajoutez vos produits dans **Produits & stocks** : prix de vente, coût d’achat, quantité et seuil d’alerte.
4. Ajoutez vos clients habituels dans **Clients & crédits**.
5. Enregistrez vos ventes. Le stock est déduit automatiquement.
6. Utilisez **Déconnexion** sur les appareils partagés.
7. Pour retrouver votre boutique sur un autre appareil, ouvrez la même adresse du service et connectez-vous au même compte.

Conservez votre mot de passe : la récupération par e-mail n’est pas encore développée. L’e-mail est utilisé comme identifiant mais son propriétaire n’est pas vérifié dans cette version.

## Page d’accueil publique

L’accueil présente les fonctionnalités, un aperçu illustratif du tableau de bord (chiffres fictifs), les problèmes traités, les trois étapes de démarrage, la séparation des espaces commerçants, l’accès pilote et une FAQ détaillée.

Le menu mène aux sections de la page. Les boutons **Commencer** et **Créer mon espace boutique** ouvrent l’inscription ; **Se connecter** ouvre la connexion. Sur téléphone, la navigation est regroupée dans le bouton menu. Le logo de la page d’inscription ou de connexion ramène à l’accueil.

Si vous êtes déjà connecté, l’application ouvre directement votre tableau de bord. Le bouton **Accueil** en haut permet de consulter la présentation sans fermer votre session. **Accéder à ma boutique** permet de revenir dans votre espace.

Le texte, les illustrations d’interface et les animations de l’accueil sont intégrés dans `index.html`. Les fichiers `landing.css`, `landing.js`, `premium.css` et `premium.js` conservent leur source séparée pour faciliter les évolutions ; le navigateur n’a pas besoin de les charger séparément.

### Design et animations premium

- Typographie variable Manrope, embarquée en WOFF2 dans le HTML : pas de requête vers Google Fonts lors de l’utilisation. Licence OFL fournie dans `assets/Manrope-LICENSE.txt`.
- Palette ivoire et vert profond, dégradés doux, ombres et cartes en relief.
- Apparitions progressives au défilement et animations d’entrée du premier écran.
- Aperçu d’interface en perspective, inclinaison subtile au pointeur sur ordinateur et cartes flottantes.
- Trois onglets d’aperçu interactifs : Vue d’ensemble, Stocks et Crédits. Les chiffres sont fictifs ; ces aperçus ne modifient aucune donnée réelle.
- Survol des boutons et des cartes, barre de progression de lecture, navigation indiquant la section active et bouton de retour en haut.
- Les onglets d’aperçu sont utilisables au clavier (flèches gauche/droite, Début/Fin).
- Les animations et l’effet de perspective sont désactivés avec le réglage système « Réduire les animations ». L’inclinaison au pointeur n’est pas activée sur écran tactile.

### Visuels de marque générés par IA

Cinq images cohérentes sont intégrées dans la palette crème, vert sauge et bois :

- `boutique-hero` : commerçante dans une alimentation générale de quartier, visuel principal de l’accueil.
- `boutique-stock` : rayonnages et réapprovisionnement alimentaire, section du catalogue et des stocks.
- `boutique-clients` : conseil d’un vendeur d’électroménager auprès d’une cliente, section de la relation client.
- `boutique-commercant` : commerçant avec tablette dans un magasin d’électroménager, présentation des espaces indépendants.
- `boutique-inscription` : portrait de la commerçante dans son alimentation générale sur l’inscription et la connexion, avec bandeau recadré sur mobile.

Ces scènes sont des illustrations générées, pas des photographies de clients réels ni des témoignages. L’interface les signale comme telles. Les fichiers JPEG sont conservés dans `assets`, ainsi que leurs versions WebP optimisées. Les images sont embarquées dans le HTML via `brand-images.js`, sans dépendance à un hébergeur d’images. Les contenus sous le premier écran utilisent le chargement différé.

L’aperçu interactif du logiciel a été conservé dans une section dédiée, distincte du visuel photographique principal. Les sources de la mise en page des images sont `brand-media.css` et `brand-media.js`.

## Ce qui a changé

- Inscription réelle, pas une simulation dans le navigateur.
- Connexion et déconnexion avec invalidation de la session côté serveur.
- Mots de passe hachés avec scrypt et sel aléatoire ; ils ne sont pas stockés en clair.
- Sessions aléatoires, stockées sous forme de condensat côté serveur, avec cookie HttpOnly.
- Base SQLite persistante sur le serveur, dans `private_data/boutiquepilot.sqlite3`.
- Les données de boutique sont liées à l’identifiant de compte fourni par la session : le client ne peut pas choisir un autre propriétaire dans une requête.
- Les API de données refusent les requêtes sans session.
- Protection contre l’écrasement silencieux lors de modifications simultanées : une version périmée est refusée. Actualisez puis recommencez.
- Aucun mot de passe ni jeu de données métier enregistré dans localStorage.

**Périmètre : plusieurs commerçants peuvent utiliser la même plateforme. Chaque compte gère une boutique indépendante.** Plusieurs magasins sous un même compte ou plusieurs employés dans la même boutique ne sont pas encore implémentés.

## Fonctionnalités de gestion conservées

Tableau de bord, graphique des ventes sur sept jours, marge brute hors charges, catalogue, stock et réapprovisionnement, alertes, ventes en espèces ou Mobile Money déclaré, ventes à crédit, fiches clients et remboursements, reçus imprimables, export CSV des produits et sauvegardes JSON de la boutique connectée.

Une vente à crédit ajoute son montant entier au crédit du client. Un acompte peut être enregistré ensuite comme remboursement. Les règlements diminuent le solde global du client, sans être affectés à une vente précise.

Les réglages **Charger une démonstration** et **Effacer les données** ne concernent que la boutique du compte connecté. Ils demandent confirmation et ne suppriment pas le compte utilisateur.

## Sauvegardes

Dans **Paramètres**, téléchargez régulièrement une sauvegarde JSON. Elle contient les produits, clients, ventes et réglages de votre boutique, mais pas votre mot de passe ni votre compte. Gardez ce fichier confidentiel.

Importer une sauvegarde remplace les données de la boutique connectée ; cela ne fusionne pas les données et ne modifie pas les autres comptes.

Pour sauvegarder toute la plateforme, l’exploitant doit aussi sauvegarder la base SQLite avec l’API de sauvegarde SQLite, par exemple depuis la racine du projet :

```bash
python - <<'PY'
import sqlite3
from datetime import datetime
source = sqlite3.connect('private_data/boutiquepilot.sqlite3')
name = 'private_data/backup-' + datetime.now().strftime('%Y%m%d-%H%M%S') + '.sqlite3'
with sqlite3.connect(name) as destination:
    source.backup(destination)
source.close()
print(name)
PY
```

Cette sauvegarde contient aussi des comptes et des sessions : elle doit être protégée, chiffrée et conservée hors du serveur. Cette commande manuelle n’est pas une sauvegarde automatique ni une politique de rétention.

## Personnaliser & outils — l’atelier du tableau de bord

Ouvrez **Personnaliser & outils** dans le menu ou avec le bouton du tableau de bord. Les fonctionnalités suivantes sont opérationnelles et propres au compte connecté.

### Reçus personnalisés

Dans **Reçus à votre image**, réglez le titre, le sous-titre, la couleur, les coordonnées à afficher, le nom du client et le message de fin. Le nom, le téléphone et l’adresse proviennent des paramètres de votre boutique.

Ajoutez un logo PNG, JPEG ou WebP (source de 3 Mo maximum). Il est redimensionné dans le navigateur puis enregistré dans les données de votre boutique. Aucun logo n’est rendu public par le serveur.

L’aperçu utilise des données fictives et ne crée pas de vente. Cliquez sur **Enregistrer le modèle** pour l’appliquer. Le modèle courant est utilisé aussi pour réimprimer les anciennes ventes ; il n’y a pas de version immuable de document conservée par vente.

### Tickets de caisse

Dans **Tickets de caisse**, choisissez une vente enregistrée puis **Ticket 80 mm** ou **Reçu A4**. Le document reprend exactement les articles, quantités, prix et montant de cette vente. Il n’ajoute pas de transaction ni d’encaissement.

Le ticket est mis en page pour un rouleau de 80 mm, avec une zone utile de 72 mm. Le navigateur doit être configuré sur le papier et l’imprimante adaptés. Le format matériel et l’export PDF dépendent du navigateur et du pilote. Aucune intégration directe à une imprimante thermique n’est incluse. Les documents ne sont pas des factures fiscales certifiées.

### Préparation comptable SYSCOHADA

Activez le module depuis l’atelier. Une entrée **Préparation comptable** apparaît dans le menu.

- Saisie manuelle d’une date, d’une référence de pièce et d’un libellé.
- De 2 à 30 lignes, avec un compte et un débit OU un crédit positif par ligne.
- Montants entiers en FCFA ; refus d’un total débit différent du total crédit, dans le navigateur et sur le serveur.
- Journal filtrable par mois, balance des mouvements et des soldes sur la période, exports CSV.
- Chaque écriture reste un **brouillon préparatoire**. Pour la corriger, supprimez-la après confirmation puis ressaisissez-la. Il n’y a pas de validation définitive ni de journal d’audit inaltérable.

Les propositions comprennent notamment les comptes 401 (fournisseurs), 411 (clients), 52 (banques), 55 (instruments de monnaie électronique), 57 (caisse), 601 (achats de marchandises) et 701 (ventes de marchandises). Ce sont des repères à adapter et subdiviser avec un comptable, pas un plan complet. Référence : [1](https://plan-comptable-ohada.com/nouvelle-norme-2016/plan-comptable-syscohada.html).

**Important : ce n’est pas une comptabilité réglementaire complète ou certifiée.** Les ventes ne sont pas synchronisées automatiquement avec le journal. Il n’y a pas de calcul de TVA, de bilan, de compte de résultat réglementaire, de clôture, d’à-nouveaux automatiques ni d’écritures d’inventaire. Une balance équilibrée ne garantit pas un traitement comptable correct. Faites valider les comptes, subdivisions et traitements par un professionnel.

### Créer votre propre outil de suivi

Cliquez sur **Créer un outil**. Donnez-lui un nom et une description puis définissez de 1 à 8 colonnes : texte, nombre, date ou statut. Deux points de départ sont proposés : livraisons et suivi de dépenses. Vous pouvez créer jusqu’à 30 outils, avec jusqu’à 10 000 lignes par outil dans la limite de taille de sauvegarde du pilote.

Une fois créé, ajoutez, modifiez, recherchez ou supprimez des lignes et exportez la fiche en CSV. Les statuts proposés sont **À faire**, **En cours** et **Terminé**. La structure des colonnes est fixée à la création.

Ce créateur produit des **fiches de suivi**, pas des logiciels arbitraires, formules, automatisations ou scripts. Les données d’une fiche ne modifient pas les ventes, le stock ou le journal. Par exemple, une dépense notée dans une fiche n’est pas comptabilisée automatiquement.

Les modèles de documents, le journal et les fiches sont inclus dans la sauvegarde JSON et restaurés avec elle. Les sauvegardes antérieures, sans champ `workspace`, restent compatibles. Une restauration remplace les réglages et données de l’atelier par ceux du fichier importé (ou par les valeurs par défaut s’ils sont absents). Exportez toujours avant de restaurer.

Les sources de cette extension sont `workspace.js`, `workspace.css` et `workspace_schema.py`. Ce dernier est **nécessaire au serveur**. Le test `test-workspace.cjs` vérifie la personnalisation, le logo, les tickets, la validation comptable, les outils, la persistance et la séparation des boutiques.

## Lancer le projet

Python 3.10+ avec prise en charge de scrypt. Aucune bibliothèque Python externe n’est nécessaire.

```bash
python server.py
```

Le serveur écoute sur `0.0.0.0:3000`. Pour changer le port :

```bash
PORT=8080 python server.py
```

Il sert uniquement les routes de l’application et les trois vidéos publiques nommées ci-dessous. Les fichiers source et la base privée ne sont pas publiés par le serveur HTTP.

Pour les tests navigateur, `test-auth.cjs` nécessite Playwright et Chromium. Le test crée des comptes fictifs de test : ne pas le lancer sur un service de production sans procédure de nettoyage.

## Avant une ouverture publique

L’aperçu Arena est un environnement de développement, **pas un hébergement permanent avec garantie de disponibilité ou de conservation des données**. Le serveur Python standard est destiné à ce pilote, pas à une exploitation publique à grande échelle.

Prévoir avant de recevoir des données réelles de clients :

- Hébergement permanent avec disque persistant, domaine stable et HTTPS obligatoire.
- Cookie Secure activé (`COOKIE_SECURE=1`) derrière un proxy HTTPS de confiance ; interdire l’accès HTTP public et configurer correctement le proxy.
- Serveur et déploiement adaptés à la production ; supervision et gestion des incidents.
- Vérification d’e-mail, récupération et changement de mot de passe.
- Politique de confidentialité, conditions d’utilisation, suppression/export de compte et obligations locales.
- Sauvegardes automatiques hors serveur, chiffrement, contrôle d’accès et tests de restauration.
- Revue de sécurité, limitation des inscriptions et protection contre l’abus adaptées au trafic. Le limiteur actuel est en mémoire et partagé par adresse réseau : il reste rudimentaire.
- Journal d’audit et opérations métier transactionnelles dédiées. Le MVP enregistre l’état entier de la boutique après chaque modification avec contrôle de version ; il n’est pas adapté à un fort volume de ventes simultanées.
- Tarification, abonnements et droits employés si nécessaires.

Mobile Money n’est pas connecté à un opérateur. Les reçus ne sont pas des factures fiscales certifiées. La marge affichée n’est pas un bénéfice net. La gestion des taxes, retours et fournisseurs reste hors périmètre. Le suivi libre de dépenses et le journal préparatoire ne remplacent pas une comptabilité complète.

## Logo d’origine conservé

Le symbole de sac et le nom BoutiquePilot restent inchangés. Le corps du sac est rempli en vert, sur le fond vert clair existant. Le réglage `brand-logo.css` est intégré au HTML et s’applique à l’accueil, aux formulaires et au tableau de bord. Le logo vectoriel est fourni dans `assets/logo-original-colore.svg`.


## Vidéo de présentation sur l’accueil

Un film animé de **20 secondes, sans son**, est intégré au visuel principal. Il présente les alimentations générales, les magasins d’électroménager, les stocks, les ventes, les crédits clients et les espaces indépendants. Il utilise des illustrations IA existantes, des mouvements de cadrage et des fondus : ce n’est pas un tournage ni une capture d’une boutique réelle. Le logo d’origine avec le sac vert est conservé.

- Ordinateur : `assets/boutiquepilot-accueil.mp4`, 900 × 720, environ 2,2 Mo.
- Téléphone : `assets/boutiquepilot-accueil-mobile.mp4`, 640 × 800, environ 1,7 Mo, sélectionné au chargement sous 601 pixels de largeur.
- Encodage H.264, 20 images par seconde, MP4 optimisé pour démarrer sans téléchargement complet ; aucune piste audio.
- Images d’attente WebP correspondantes, embarquées dans le HTML pour l’aperçu statique et la préférence de réduction des animations.
- Bouton Lire/Pause et barre de position utilisables au clavier ; lien **Découvrir en 20 secondes** depuis le texte d’accueil.
- Lecture silencieuse en boucle uniquement lorsque le visuel est suffisamment visible. Pause hors écran et quand l’onglet est masqué. Les ressources sont libérées en quittant l’accueil.
- Aucune lecture ni requête MP4 automatique si « Réduire les animations » ou l’économie de données du navigateur est activée. Le bouton Lire reste disponible. La lecture automatique dépend aussi des permissions du navigateur.
- Aucun lecteur tiers, aucune musique et aucune donnée de client dans le film.

Les deux MP4 du film de présentation et le MP4 du titre animé sont les seuls fichiers vidéo exposés par le serveur, via une liste explicite. Il prend en charge GET, HEAD et les plages d’octets (HTTP 206) pour la lecture et le déplacement dans la vidéo. La base privée et les sources restent inaccessibles. Le HTML téléchargé seul ne contient pas les MP4 : utilisez le serveur pour la lecture intégrée, ou ouvrez les vidéos séparément.

Les sources `hero-video.js` et `hero-video.css` sont intégrées dans `index.html`. `create_home_video.py` permet de recréer les deux MP4 et leurs images d’attente ; cette opération facultative demande `pip install Pillow imageio-ffmpeg`. Ces bibliothèques ne sont pas nécessaires pour lancer l’application ou lire les vidéos déjà fournies. Après une modification des sources ou des images d’attente, réintégrer les sources dans le HTML. Le test `test-home-video.cjs` couvre la lecture, les formats, les plages HTTP, les commandes, la navigation, le téléphone et le réglage de réduction des animations.


### Le titre d’accueil remplacé par une vidéo typographique

À la demande de l’utilisateur, le titre visible « Votre boutique / mérite mieux / qu’un cahier. » est maintenant **remplacé à sa place par un véritable MP4 animé** de 8 secondes : `assets/boutiquepilot-titre-anime.mp4` (960 × 480, environ 74 ko, sans son). Les lignes apparaissent progressivement et le mot « cahier » est souligné en vert. Le film se termine sur la phrase complète, sans boucle automatique. Les boutons Lire, Pause et Revoir permettent de contrôler sa lecture.

Un titre H1 équivalent reste disponible pour les lecteurs d’écran. Son image d’attente complète est embarquée dans le HTML et reste lisible si la vidéo n’est pas disponible ou si la lecture automatique est désactivée. Le réglage de réduction des animations et l’économie de données empêchent le téléchargement et la lecture automatiques. La lecture est mise en pause lorsque le titre ou l’onglet n’est plus visible.

La vidéo de présentation des commerces, à droite sur ordinateur et plus bas sur téléphone, reste conservée. Le logo n’est pas modifié.

Sources : `title-video.js`, `title-video.css` (intégrées au HTML). Recréation du film et de l’image d’attente : `python create_title_video.py`, avec les mêmes dépendances facultatives que le générateur du film précédent. Tests : `test-title-video.cjs` et les régressions de l’accueil. Après toute modification du poster, mettre également à jour sa version embarquée dans `title-video.js` et `index.html`.
