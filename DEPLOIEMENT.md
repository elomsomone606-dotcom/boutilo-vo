# Boutilo : préparation Vercel et Supabase

Cette configuration est préparée mais n'a pas encore été validée sur un déploiement Vercel ou un projet Supabase réel. Commencez par des données fictives. Le système d'authentification reste celui du serveur Python : Supabase Auth n'est pas utilisé.

## Avant de commencer

Créez un projet Supabase et un compte Vercel. Une adresse gratuite `*.vercel.app` est attribuée au projet ; aucun domaine personnel n'est nécessaire. Les limites et conditions des offres gratuites peuvent évoluer.

## Base de données

Dans l'éditeur SQL du projet Supabase, exécutez `schema-supabase.sql`. Il crée le schéma privé `boutique_private` et les tables utilisées par le serveur, sans les exposer aux rôles publics Supabase. Cette opération prépare une base vide : elle ne migre pas une base SQLite existante. Avant une migration réelle, exportez et sauvegardez les données et faites une migration contrôlée.

Récupérez dans Supabase la chaîne de connexion PostgreSQL du pooler compatible avec les connexions serveur sans état (mode transaction), en utilisant son hôte et son port réels. Conservez le mot de passe et l'URL dans un endroit sûr : ne les envoyez pas dans le chat et ne les commitez pas. Le pilote exige une connexion TLS avec vérification du certificat et du nom d'hôte (`verify-full`). Testez la connexion et les permissions réelles du rôle utilisé ; elles ne sont pas encore vérifiées.

## Vercel

Importez le dépôt contenant ce dossier dans Vercel, ou déployez-le avec les outils Vercel. Définissez `DATABASE_URL` comme variable d'environnement **côté serveur** dans les paramètres du projet, avec la chaîne PostgreSQL du pooler. Définissez aussi `COOKIE_SECURE=1`. Ne créez pas de variable préfixée `NEXT_PUBLIC_` pour ces valeurs. Redéployez après tout changement de variables.

`vercel.json` exécute `build_vercel.py` : seul `index.html` et les trois vidéos sont copiés vers `public`. L'API Python est dans `api/[...path].py`. Les fichiers serveur, les scripts et la base locale ne doivent pas être publiés comme fichiers statiques.

## Vérification après déploiement

Avec des comptes fictifs, vérifiez la page d'accueil et les vidéos, puis créez deux comptes et contrôlez l'isolation des boutiques, l'ajout d'un produit, une vente, la sauvegarde, la reconnexion et la déconnexion. Vérifiez qu'une modification périmée est refusée et que les fichiers `server.py` et `schema-supabase.sql` ne sont pas accessibles depuis le site. Testez les partages WhatsApp volontairement. Consultez les journaux Vercel en cas d'échec sans publier de données sensibles.

Le limiteur de tentatives actuel est en mémoire : il ne protège pas efficacement plusieurs instances serverless. L'e-mail n'est pas vérifié et la récupération du mot de passe n'est pas implémentée. Ajoutez un limiteur partagé, la récupération de compte, des sauvegardes vérifiées et une revue de sécurité avant d'accepter des données réelles. Les limites de taille et de durée des fonctions Vercel peuvent aussi nécessiter une adaptation des sauvegardes volumineuses. Les paiements Mobile Money sont uniquement déclarés manuellement.

Pour le développement local sans PostgreSQL : `python server.py`. Cela crée une base SQLite dans `private_data/`. Cette base locale et la base Supabase sont indépendantes.
