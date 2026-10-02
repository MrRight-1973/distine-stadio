"""Pubblicazione della distinta su un repository GitHub (servito da GitHub Pages).

Tutti i file vengono scritti in UN SOLO commit, così la pagina pubblica non può
mai mostrare un JSON nuovo con un PDF vecchio (o viceversa) e GitHub Pages
ricostruisce il sito una volta sola.

Il token deve essere un "fine-grained personal access token" limitato al solo
repository della pagina, con il permesso "Contents: Read and write".
"""
import base64

import requests

GITHUB_API = "https://api.github.com"


class PubblicazioneErrore(Exception):
    """Errore comprensibile da mostrare alla segreteria."""


def _intestazioni(token):
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


def _chiama(metodo, url, token, timeout, **kwargs):
    try:
        r = requests.request(metodo, url, headers=_intestazioni(token), timeout=timeout, **kwargs)
    except requests.RequestException as e:
        raise PubblicazioneErrore(f"GitHub non raggiungibile: {e}") from e

    if r.status_code in (401, 403):
        raise PubblicazioneErrore(
            "GitHub ha rifiutato il token (GITHUB_TOKEN scaduto, errato o senza il permesso "
            "'Contents: Read and write' sul repository)."
        )
    if r.status_code == 404:
        raise PubblicazioneErrore(
            "Repository o ramo non trovato: controlla GITHUB_REPO e GITHUB_BRANCH, e che il token "
            "abbia accesso a quel repository."
        )
    if r.status_code == 409:
        raise PubblicazioneErrore(
            "Il repository è vuoto: carica prima almeno un file (per esempio index.html)."
        )
    return r


def pubblica_su_github(token, repo, file_da_pubblicare, messaggio, branch="main",
                       api_base=GITHUB_API, timeout=20):
    """Scrive i file nel repository con un solo commit.

    file_da_pubblicare: dict {percorso_nel_repo: contenuto in bytes}
    Restituisce lo sha del nuovo commit.
    """
    if not token or not repo:
        raise PubblicazioneErrore("GITHUB_TOKEN o GITHUB_REPO non configurati nei secrets.")
    if not file_da_pubblicare:
        raise PubblicazioneErrore("Nessun file da pubblicare.")

    base = f"{api_base}/repos/{repo}"

    for tentativo in range(2):  # secondo giro solo se qualcuno ha scritto nel frattempo
        # 1) ultimo commit del ramo
        r = _chiama("GET", f"{base}/git/ref/heads/{branch}", token, timeout)
        if r.status_code != 200:
            raise PubblicazioneErrore(f"Lettura del ramo '{branch}' fallita (HTTP {r.status_code}).")
        sha_commit = r.json()["object"]["sha"]

        r = _chiama("GET", f"{base}/git/commits/{sha_commit}", token, timeout)
        if r.status_code != 200:
            raise PubblicazioneErrore(f"Lettura del commit fallita (HTTP {r.status_code}).")
        sha_albero = r.json()["tree"]["sha"]

        # 2) un blob per ogni file
        voci = []
        for percorso, contenuto in file_da_pubblicare.items():
            r = _chiama(
                "POST", f"{base}/git/blobs", token, timeout,
                json={"content": base64.b64encode(contenuto).decode("ascii"), "encoding": "base64"},
            )
            if r.status_code != 201:
                raise PubblicazioneErrore(f"Caricamento di {percorso} fallito (HTTP {r.status_code}).")
            voci.append({"path": percorso, "mode": "100644", "type": "blob", "sha": r.json()["sha"]})

        # 3) nuovo albero, nuovo commit, aggiornamento del ramo
        r = _chiama("POST", f"{base}/git/trees", token, timeout,
                    json={"base_tree": sha_albero, "tree": voci})
        if r.status_code != 201:
            raise PubblicazioneErrore(f"Creazione dell'albero fallita (HTTP {r.status_code}).")
        nuovo_albero = r.json()["sha"]

        r = _chiama("POST", f"{base}/git/commits", token, timeout,
                    json={"message": messaggio, "tree": nuovo_albero, "parents": [sha_commit]})
        if r.status_code != 201:
            raise PubblicazioneErrore(f"Creazione del commit fallita (HTTP {r.status_code}).")
        nuovo_commit = r.json()["sha"]

        r = _chiama("PATCH", f"{base}/git/refs/heads/{branch}", token, timeout,
                    json={"sha": nuovo_commit, "force": False})
        if r.status_code == 200:
            return nuovo_commit
        if r.status_code == 422 and tentativo == 0:
            continue  # il ramo si è mosso: si riparte dall'ultimo commit
        raise PubblicazioneErrore(f"Aggiornamento del ramo fallito (HTTP {r.status_code}).")

    raise PubblicazioneErrore("Pubblicazione non riuscita: riprova tra qualche istante.")


def url_pagina_da_repo(repo):
    """URL standard di GitHub Pages per un repository 'utente/nome'."""
    try:
        utente, nome = repo.split("/", 1)
    except (ValueError, AttributeError):
        return None
    if nome.lower() == f"{utente.lower()}.github.io":
        return f"https://{utente}.github.io/"
    return f"https://{utente}.github.io/{nome}/"
