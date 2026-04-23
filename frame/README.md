# Framily Frame

## Installation et configuration

Install necessary packages and enable SPI interface:

```sh
sudo apt-get update
sudo apt-get install -y python3-pil python3-qrcode python3-flask python3-inotify fonts-dejavu python3-pip
sudo pip3 install --break-system-packages urlpath
sudo raspi-config nonint do_spi 0
sudo reboot
```



#### 1. **Mise en service initiale**
- **État initial** : Le cadre arrive préinstallé avec un système d'exploitation configuré sur la Raspberry Pi Zero W et un écran e-ink fonctionnel.
- **Mode AP (Access Point)** : Au premier démarrage, le cadre crée un hotspot géré par NetworkManager (ex: "FramilyFrame-D8Z3") et affiche sur l'écran les informations de connexion (SSID et mot de passe).
- **Page d'initialisation** : Une fois connecté à ce réseau, l'utilisateur accède à une page web servie par le cadre (ex: `http://192.168.50.1:8000`). Cette page permet de :
  - Saisir les informations du réseau Wi-Fi domestique (SSID et mot de passe).
  - Saisir l'URL du serveur self-hosté (ex: `https://mon-serveur-photo.fr` ou une IP locale si le serveur est sur le même réseau).
  - Valider les informations.

#### 2. **Connexion et vérification**
- **Connexion au Wi-Fi** : Le cadre tente de se connecter au réseau Wi-Fi domestique avec les informations fournies.
- **Test d'accès au serveur** : Une fois connecté au Wi-Fi, il vérifie l'accès au serveur en envoyant une requête de test (ex: `GET /api/ping`).
  - **En cas d'échec** : Retour à la page d'initialisation avec un message d'erreur précis (ex: "Impossible de se connecter au Wi-Fi", "Serveur inaccessible", "URL invalide").
  - **En cas de succès** : Passage à l'étape suivante.

#### 3. **Création de l'identifiant du cadre**
- **Requête d'enregistrement** : Le cadre envoie une requête au serveur pour créer un identifiant unique (ex: `POST /api/register` avec un payload contenant un nom par défaut comme "CadrePhoto_Famille1").
- **Affichage de l'identifiant** : L'écran affiche l'identifiant généré (ex: "ID : FAM12345") et un QR code pour faciliter l'ajout par les utilisateurs.
- **Attente de la première connexion utilisateur** : Le cadre reste dans cet état jusqu'à ce qu'un utilisateur se connecte à la famille via le serveur.

#### 4. **Mode opérationnel**
- **Première photo** : Dès qu'un utilisateur est associé à la famille, le cadre affiche un message du type : "Félicitations ! Ajoutez une première photo via l'application ou le site web."
- **Fonctionnement normal** : Le cadre commence à récupérer régulièrement des photos depuis le serveur (ex: toutes les 5 minutes via `GET /api/photos?frame_id=FAM12345`).
  - **Gestion des erreurs** : En cas de problème (perte de connexion Wi-Fi, serveur inaccessible), le cadre revient en mode hotspot géré par NetworkManager après plusieurs tentatives infructueuses, affichant un message d'erreur et permettant une nouvelle configuration.

#### 5. **Gestion des erreurs et récupération**
- **Reconfiguration automatique** : Si le cadre détecte une erreur persistante (ex: Wi-Fi indisponible pendant 24h), il revient en mode hotspot géré par NetworkManager pour permettre une reconfiguration.
- **Reconnexion automatique** : En parallèle, il tente périodiquement de se reconnecter au Wi-Fi et au serveur sans intervention utilisateur.
