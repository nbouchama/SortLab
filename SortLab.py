#!/usr/bin/env python3
"""SortLab : un outil interactif de visualisation des algorithmes de tri.

Lancement avec Python 3.8 ou ultérieur. L’interface repose sur les composants
classiques de Tkinter et ttk.
"""
import csv
import math
import operator
import random
import time
import json
import tkinter as tk
from tkinter import filedialog, messagebox, ttk
from tkinter.scrolledtext import ScrolledText


# ======================================================================
#  Algorithmes (générateurs). Chaque yield renvoie un triplet
#      (opération, indices, détail)
#    "info" : message d'explication (détail = texte), sans effet sur les statistiques
#    "cmp"  : comparaison ; détail = (x, y, test, si_oui, si_non[, (lib_x, lib_y)])
#    "swap" : échange de deux cases ; détail = (valeur_case_1, valeur_case_2) AVANT l'échange
#    "set"  : écriture dans une case (tri fusion) ; détail = (valeur, moitié, reste?)
# ======================================================================
def tri_bulles_naif(a):
    """Version naïve : fait toujours les n−1 passes, même si le tableau est déjà trié."""
    n = len(a)
    for i in range(n - 1):
        yield "info", (), (f"Passe {i + 1}/{n - 1} : on compare les voisins des cases 1 à {n - i}. "
                           f"Le plus grand élément restant va « remonter » jusqu'en case {n - i}.")
        echange = False
        for j in range(n - 1 - i):
            yield "cmp", (j, j + 1), (a[j], a[j + 1], ">",
                                      "mal ordonnées : on les échange",
                                      "déjà dans l'ordre : on avance d'une case")
            if a[j] > a[j + 1]:
                x, y = a[j], a[j + 1]
                a[j], a[j + 1] = y, x
                echange = True
                yield "swap", (j, j + 1), (x, y)
        if not echange and i < n - 2:
            yield "info", (), ("Aucun échange pendant cette passe, mais la version naïve ne le remarque pas : "
                               "elle continue toutes les passes prévues.")
        yield "info", (), (f"Fin de la passe {i + 1} : la valeur {a[n - 1 - i]} est à sa place "
                           f"définitive (case {n - i}).")


def tri_bulles_anticipe(a):
    """Version optimisée : s'arrête dès qu'une passe complète se termine sans aucun échange."""
    n = len(a)
    for i in range(n - 1):
        yield "info", (), (f"Passe {i + 1}/{n - 1} : on compare les voisins des cases 1 à {n - i}. "
                           f"Le plus grand élément restant va « remonter » jusqu'en case {n - i}.")
        echange = False
        for j in range(n - 1 - i):
            yield "cmp", (j, j + 1), (a[j], a[j + 1], ">",
                                      "mal ordonnées : on les échange",
                                      "déjà dans l'ordre : on avance d'une case")
            if a[j] > a[j + 1]:
                x, y = a[j], a[j + 1]
                a[j], a[j + 1] = y, x
                echange = True
                yield "swap", (j, j + 1), (x, y)
        if not echange:
            yield "info", (), "Aucun échange pendant cette passe : le tableau est trié, on s'arrête (arrêt anticipé)."
            break
        yield "info", (), (f"Fin de la passe {i + 1} : la valeur {a[n - 1 - i]} est à sa place "
                           f"définitive (case {n - i}).")


def tri_selection(a):
    n = len(a)
    for i in range(n - 1):
        yield "info", (), (f"Étape {i + 1}/{n - 1} : recherche du minimum parmi les cases "
                           f"{i + 1} à {n} pour le placer en case {i + 1}.")
        m = i
        for j in range(i + 1, n):
            yield "cmp", (m, j), (a[m], a[j], ">",
                                  "nouveau minimum : la case {j} (valeur {y}) devient le minimum courant",
                                  "le minimum courant (case {i}, valeur {x}) reste inchangé")
            if a[j] < a[m]:
                m = j
        if m != i:
            x, y = a[i], a[m]
            yield "info", (), (f"Le minimum est la valeur {y} (case {m + 1}) : "
                               f"on l'échange avec la case {i + 1}.")
            a[i], a[m] = y, x
            yield "swap", (i, m), (x, y)
        else:
            yield "info", (), (f"Le minimum (valeur {a[i]}) est déjà en case {i + 1} : aucun échange.")


def tri_insertion(a):
    for i in range(1, len(a)):
        yield "info", (), (f"Insertion de la valeur {a[i]} (case {i + 1}) dans la partie gauche "
                           f"déjà triée (cases 1 à {i}).")
        j = i
        while j > 0:
            yield "cmp", (j - 1, j), (a[j - 1], a[j], ">",
                                      "{x} est plus grand que {y} : on échange pour décaler vers la droite",
                                      "bon ordre : la valeur est à sa place, fin de l'insertion")
            if a[j - 1] > a[j]:
                x, y = a[j - 1], a[j]
                a[j - 1], a[j] = y, x
                yield "swap", (j - 1, j), (x, y)
                j -= 1
            else:
                break


def tri_shell(a):
    n = len(a)
    ecart = n // 2
    while ecart > 0:
        yield "info", (), (f"Écart {ecart} : on trie par insertion les cases séparées de {ecart} "
                           f"(1, {1 + ecart}, {1 + 2 * ecart}...).")
        for i in range(ecart, n):
            j = i
            while j >= ecart:
                yield "cmp", (j - ecart, j), (a[j - ecart], a[j], ">",
                                              "mal ordonnées : on échange",
                                              "bon ordre : on passe à l'élément suivant")
                if a[j - ecart] > a[j]:
                    x, y = a[j - ecart], a[j]
                    a[j - ecart], a[j] = y, x
                    yield "swap", (j - ecart, j), (x, y)
                    j -= ecart
                else:
                    break
        ecart //= 2


def tri_rapide(a):
    pile = [(0, len(a) - 1)]
    while pile:
        lo, hi = pile.pop()
        if lo >= hi:
            continue
        pivot = a[hi]
        yield "info", (hi,), (f"Partition des cases {lo + 1} à {hi + 1} : pivot = valeur {pivot} "
                           f"(case {hi + 1}). Les plus petits iront à gauche, les autres à droite.")
        i = lo
        for j in range(lo, hi):
            yield "cmp", (j, hi), (a[j], pivot, "<",
                                   "{x} < pivot : va dans la zone des petits (à gauche)",
                                   "{x} ≥ pivot : reste dans la zone des grands (à droite)")
            if a[j] < pivot:
                if i != j:
                    x, y = a[i], a[j]
                    a[i], a[j] = y, x
                    yield "swap", (i, j), (x, y)
                i += 1
        if i != hi:
            x, y = a[i], a[hi]
            a[i], a[hi] = y, x
            yield "swap", (i, hi), (x, y)
        yield "info", (), f"Le pivot {pivot} est à sa place définitive : case {i + 1}."
        pile.append((lo, i - 1))
        pile.append((i + 1, hi))


def tri_fusion(a, lo=0, hi=None):
    if hi is None:
        hi = len(a) - 1
    if lo >= hi:
        return
    mid = (lo + hi) // 2
    yield from tri_fusion(a, lo, mid)
    yield from tri_fusion(a, mid + 1, hi)
    gauche, droite = a[lo:mid + 1], a[mid + 1:hi + 1]
    yield "info", (), (f"Fusion de la moitié gauche (cases {lo + 1}–{mid + 1}) {gauche} et de la "
                       f"moitié droite (cases {mid + 2}–{hi + 1}) {droite}, déjà triées chacune.")
    i = j = 0
    k = lo
    while i < len(gauche) and j < len(droite):
        yield "cmp", (lo + i, mid + 1 + j), (gauche[i], droite[j], "<=",
                                             "on prend {x} (moitié gauche) car il est ≤ {y}",
                                             "on prend {y} (moitié droite) car {x} > {y}",
                                             ("gauche", "droite"))
        if gauche[i] <= droite[j]:
            v, cote = gauche[i], "gauche"
            i += 1
        else:
            v, cote = droite[j], "droite"
            j += 1
        a[k] = v
        yield "set", (k,), (v, cote, False)
        k += 1
    for cote, reste in (("gauche", gauche[i:]), ("droite", droite[j:])):
        for v in reste:
            a[k] = v
            yield "set", (k,), (v, cote, True)
            k += 1
    yield "info", (), f"Cases {lo + 1} à {hi + 1} maintenant triées : {a[lo:hi + 1]}."


ALGOS = {
    "Tri à bulles (naïf)": tri_bulles_naif,
    "Tri à bulles (arrêt anticipé)": tri_bulles_anticipe,
    "Tri par sélection": tri_selection,
    "Tri par insertion": tri_insertion,
    "Tri de Shell": tri_shell,
    "Tri rapide (quicksort)": tri_rapide,
    "Tri fusion": tri_fusion,
}

ALGO_INFO = {
    "Tri à bulles (naïf)": ("O(n²) dans tous les cas",
                            "Comparer les voisins deux à deux et fait « remonter » le plus grand élément à "
                            "chaque passe. Version naïve : fait toujours les n−1 passes, même si le "
                            "tableau est déjà trié."),
    "Tri à bulles (arrêt anticipé)": ("O(n²), O(n) si déjà trié",
                                      "Même principe, mais s'arrête dès qu'une passe se termine sans aucun "
                                      "échange : très rapide sur un tableau presque trié."),
    "Tri par sélection": ("O(n²)",
                          "Cherche le minimum du reste du tableau puis le place en tête. Très peu "
                          "d'échanges (au plus n−1) mais toujours beaucoup de comparaisons."),
    "Tri par insertion": ("O(n²), rapide si presque trié",
                          "Insère chaque élément à sa place dans la partie gauche déjà triée, comme "
                          "on range des cartes dans sa main."),
    "Tri de Shell": ("environ O(n^1,3)",
                     "Insertion avec des écarts décroissants : les éléments très mal placés "
                     "voyagent vite vers leur zone finale."),
    "Tri rapide (quicksort)": ("O(n log n) en moyenne",
                               "Choisit un pivot, envoie les petits à gauche et les grands à droite, "
                               "puis recommence sur chaque côté."),
    "Tri fusion": ("O(n log n) garanti",
                   "Coupe en deux, trie chaque moitié puis les fusionne. N'échange pas de cases : "
                   "il écrit des valeurs (colonne « Écritures »)."),
}

COULEURS_ALGOS = ["#3B82F6", "#6366F1", "#EF4444", "#10B981", "#F59E0B", "#8B5CF6", "#14B8A6"]
TESTS = {">": operator.gt, "<": operator.lt, "<=": operator.le}


NOMS_COURTS = {"Tri à bulles (naïf)": "Bulles naïf",
               "Tri à bulles (arrêt anticipé)": "Bulles anticipé"}


def nom_court(nom):
    if nom in NOMS_COURTS:
        return NOMS_COURTS[nom]
    court = nom.split(" (")[0]
    for prefixe in ("Tri à ", "Tri par ", "Tri de ", "Tri "):
        if court.startswith(prefixe):
            court = court[len(prefixe):]
            break
    return court.capitalize()


def decrire(op, idx, extra):
    """Phrase verbose décrivant une étape (cmp / swap / set)."""
    if op == "cmp":
        x, y, test, oui, non = extra[:5]
        res = TESTS[test](x, y)
        i, j = idx[0] + 1, idx[1] + 1
        if len(extra) > 5:
            lx, ly = extra[5]
            debut = (f"Comparer le plus petit restant de la moitié {lx} (valeur {x}) "
                     f"et de la moitié {ly} (valeur {y})")
        else:
            debut = f"Comparer case {i} (valeur {x}) et case {j} (valeur {y})"
        suite = (oui if res else non).format(i=i, j=j, x=x, y=y)
        return f"{debut} : {x} {test} {y} ? {'OUI' if res else 'NON'} → {suite}"
    if op == "swap":
        x, y = extra
        return (f"Échange : la valeur {x} (case {idx[0] + 1}) et la valeur {y} "
                f"(case {idx[1] + 1}) permutent")
    v, cote, reste = extra
    k = idx[0] + 1
    if cote in ("tri par comptage", "passe radix"):
        return f"Écrit la valeur {v} en case {k} ({cote})"
    if reste:
        return f"Recopie le reste de la moitié {cote} : valeur {v} en case {k}"
    return f"Écrit la valeur {v} en case {k} (prise dans la moitié {cote})"


# ======================================================================
#  Statistiques
# ======================================================================
class Stats:
    """Compteurs globaux, par case, et historique cumulé au fil des étapes."""

    def __init__(self, n):
        self.n = n
        self.etapes = 0
        self.cmp = 0
        self.swap = 0
        self.set = 0
        self.mv = 0            # cases déplacées (échange = 2 cases, écriture = 1)
        self.dist = 0          # somme des distances |i-j| des échanges
        self.temps = 0.0
        self.pos_mv = [0] * n
        self.pos_cmp = [0] * n
        self.hist_cmp = [0]
        self.hist_mv = [0]

    def add(self, op, idx):
        self.etapes += 1
        if op == "cmp":
            self.cmp += 1
            for i in idx:
                self.pos_cmp[i] += 1
        elif op == "swap":
            self.swap += 1
            self.mv += 2
            self.dist += abs(idx[0] - idx[1])
            for i in idx:
                self.pos_mv[i] += 1
        else:
            self.set += 1
            self.mv += 1
            self.pos_mv[idx[0]] += 1
        self.hist_cmp.append(self.cmp)
        self.hist_mv.append(self.mv)

    def case_top(self):
        if not self.pos_mv or max(self.pos_mv) == 0:
            return "—"
        m = max(self.pos_mv)
        return f"n°{self.pos_mv.index(m) + 1} ({m}×)"


def executer(algo, valeurs):
    """Exécute un algo sans animation : renvoie ses statistiques complètes."""
    a = list(valeurs)
    t0 = time.perf_counter()
    for _ in algo(a):
        pass
    temps = time.perf_counter() - t0
    a = list(valeurs)
    s = Stats(len(a))
    for op, idx, _ in algo(a):
        if op != "info":
            s.add(op, idx)
    s.temps = temps
    return s



# ======================================================================
#  Interface Tkinter standard et outils pédagogiques complémentaires
# ======================================================================


def tri_cocktail(a):
    """Tri à bulles bidirectionnel."""
    left, right = 0, len(a) - 1
    while left < right:
        changed = False
        yield "info", (), f"Parcours vers la droite des positions {left + 1} à {right + 1}."
        for i in range(left, right):
            yield "cmp", (i, i + 1), (a[i], a[i + 1], ">", "désordonnées : les échanger", "dans l’ordre : continuer")
            if a[i] > a[i + 1]:
                x, y = a[i], a[i + 1]
                a[i], a[i + 1] = y, x
                changed = True
                yield "swap", (i, i + 1), (x, y)
        if not changed:
            break
        right -= 1
        changed = False
        yield "info", (), f"Parcours vers la gauche des positions {right + 1} à {left + 1}."
        for i in range(right, left, -1):
            yield "cmp", (i - 1, i), (a[i - 1], a[i], ">", "désordonnées : les échanger", "dans l’ordre : continuer")
            if a[i - 1] > a[i]:
                x, y = a[i - 1], a[i]
                a[i - 1], a[i] = y, x
                changed = True
                yield "swap", (i - 1, i), (x, y)
        if not changed:
            break
        left += 1


def tri_tas(a):
    """Tri en place par tas maximum."""
    n = len(a)
    def sift(size, root):
        while True:
            largest = root
            child = 2 * root + 1
            if child < size:
                yield "cmp", (largest, child), (a[largest], a[child], "<", "le fils est plus grand", "la racine reste plus grande")
                if a[child] > a[largest]:
                    largest = child
            if child + 1 < size:
                yield "cmp", (largest, child + 1), (a[largest], a[child + 1], "<", "le fils droit est plus grand", "la valeur candidate reste plus grande")
                if a[child + 1] > a[largest]:
                    largest = child + 1
            if largest == root:
                return
            x, y = a[root], a[largest]
            a[root], a[largest] = y, x
            yield "swap", (root, largest), (x, y)
            root = largest
    for root in range(n // 2 - 1, -1, -1):
        yield from sift(n, root)
    for end in range(n - 1, 0, -1):
        x, y = a[0], a[end]
        a[0], a[end] = y, x
        yield "swap", (0, end), (x, y)
        yield from sift(end, 0)


def tri_comptage(a):
    """Tri par comptage stable, compatible avec les entiers négatifs."""
    if not a:
        return
    low, high = min(a), max(a)
    if high - low > 100000:
        # Évite d'allouer un tableau de compteurs disproportionné pour des valeurs très espacées.
        yield "info", (), "La plage est trop large pour le tri par comptage ; le tri fusion est utilisé pour éviter une allocation excessive."
        yield from tri_fusion(a)
        return
    counts = [0] * (high - low + 1)
    for value in a:
        counts[value - low] += 1
    yield "info", (), f"Tri par comptage : plage de valeurs de {low} à {high}."
    out = 0
    for décalage, count in enumerate(counts):
        for _ in range(count):
            value = décalage + low
            a[out] = value
            yield "set", (out,), (value, "tri par comptage", False)
            out += 1


def tri_radix(a):
    """Tri radix stable en base 10, compatible avec les entiers positifs et négatifs."""
    if not a:
        return
    low = min(a)
    keys = [value - low for value in a]
    maximum = max(keys)
    place = 1
    while maximum // place:
        buckets = [[] for _ in range(10)]
        for value, key in zip(a, keys):
            buckets[(key // place) % 10].append((value, key))
        ordered = [pair for bucket in buckets for pair in bucket]
        yield "info", (), f"Passe radix sur le chiffre de rang {place} (décalage {low} pour gérer les valeurs négatives)."
        for i, (value, key) in enumerate(ordered):
            a[i] = value
            yield "set", (i,), (value, "passe radix", False)
        keys = [key for _, key in ordered]
        place *= 10


ALGOS.update({
    "Tri cocktail": tri_cocktail,
    "Tri par tas": tri_tas,
    "Tri par comptage": tri_comptage,
    "Tri radix": tri_radix,
})
ALGO_INFO.update({
    "Tri cocktail": ("O(n²), O(n) dans le meilleur cas", "Parcourt le tableau dans les deux sens pour déplacer alternativement les grandes et les petites valeurs."),
    "Tri par tas": ("O(n log n) garanti", "Construit un tas maximum puis place sa plus grande valeur à la fin. Il est en place et instable."),
    "Tri par comptage": ("O(n + k)", "Compte les occurrences dans une plage entière bornée, puis réécrit les valeurs dans l’ordre. Stable et sans comparaisons entre valeurs."),
    "Tri radix": ("O(d(n + b))", "Trie par passes stables sur les chiffres, sans comparer les valeurs. La translation prend aussi en charge les entiers négatifs."),
})
NOMS_COURTS.update({"Tri cocktail": "Cocktail", "Tri par tas": "Tas", "Tri par comptage": "Comptage", "Tri radix": "Radix"})
COULEURS_ALGOS.extend(["#0891B2", "#7C3AED", "#65A30D", "#DB2777"])
ALGO_PROPERTIES = {
    "Tri à bulles (naïf)": ("Oui", "Oui", "O(n²) / O(n²) / O(n²)"),
    "Tri à bulles (arrêt anticipé)": ("Oui", "Oui", "O(n) / O(n²) / O(n²)"),
    "Tri par sélection": ("Non", "Oui", "O(n²) / O(n²) / O(n²)"),
    "Tri par insertion": ("Oui", "Oui", "O(n) / O(n²) / O(n²)"),
    "Tri de Shell": ("Non", "Oui", "Dépend de la suite des écarts"),
    "Tri rapide (quicksort)": ("Non", "Oui", "O(n log n) / O(n log n) / O(n²)"),
    "Tri fusion": ("Oui", "Non", "O(n log n) / O(n log n) / O(n log n)"),
    "Tri cocktail": ("Oui", "Oui", "O(n) / O(n²) / O(n²)"),
    "Tri par tas": ("Non", "Oui", "O(n log n) / O(n log n) / O(n log n)"),
    "Tri par comptage": ("Oui", "Non", "O(n + k) / O(n + k) / O(n + k)"),
    "Tri radix": ("Oui", "Non", "O(d(n + b))"),
}

PROFILS = ("Aléatoire", "Déjà trié", "Trié à l’envers", "Presque trié", "Avec doublons", "Peu de valeurs distinctes", "Valeurs négatives", "Valeurs personnalisées")


class App:
    """Visualiseur de tri doté d'une interface de bureau Tkinter classique."""
    def __init__(self, root):
        self.root = root
        self.root.title("SortLab — Visualiseur d’algorithmes de tri")
        self.root.geometry("1180x820")
        self.root.minsize(900, 650)
        self.style = ttk.Style(root)
        try:
            self.style.theme_use("vista")
        except tk.TclError:
            self.style.theme_use("clam")
        self.style.configure("Title.TLabel", font=("TkDefaultFont", 15, "bold"))
        self.style.configure("Subtle.TLabel", foreground="#555555")
        self.values, self.initial = [], []
        self.profile = tk.StringVar(value=PROFILS[0])
        self.algorithm = tk.StringVar(value=list(ALGOS)[0])
        self.count = tk.IntVar(value=30)
        self.speed = tk.IntVar(value=50)
        self.shape_mode = tk.StringVar(value="Boules")
        self.status = tk.StringVar(value="Prêt")
        self.verbose = tk.BooleanVar(value=True)
        self.show_comparisons = tk.BooleanVar(value=True)
        self.stats = Stats(0)
        self.gen = None
        self.running = False
        self.paused = False
        self.timer = None
        self.history = []
        self.last_indices = ()
        self.last_op = None
        self.start_time = 0.0
        self.elapsed = 0.0
        self.results = []
        self.drag_index = None
        self.race = None
        self.race_timer = None
        self.challenge_values = []
        self.benchmarks = []
        self._build()
        self.bind_keys()
        self.new_data()

    def _build(self):
        outer = ttk.Frame(self.root, padding=10)
        outer.pack(fill="both", expand=True)
        header = ttk.Frame(outer)
        header.pack(fill="x", pady=(0, 8))
        ttk.Label(header, text="SortLab", style="Title.TLabel").pack(side="left")
        ttk.Label(header, text="Visualiseur d’algorithmes de tri", style="Subtle.TLabel").pack(side="left", padx=12)
        ttk.Button(header, text="Ouvrir une expérience…", command=self.open_experiment).pack(side="right", padx=3)
        ttk.Button(header, text="Enregistrer une expérience…", command=self.save_experiment).pack(side="right", padx=3)

        self.tabs = ttk.Notebook(outer)
        self.tabs.pack(fill="both", expand=True)
        self.tab_sort = ttk.Frame(self.tabs, padding=8)
        self.tab_stats = ttk.Frame(self.tabs, padding=8)
        self.tab_compare = ttk.Frame(self.tabs, padding=8)
        self.tab_complexity = ttk.Frame(self.tabs, padding=8)
        self.tab_challenge = ttk.Frame(self.tabs, padding=8)
        self.tab_help = ttk.Frame(self.tabs, padding=8)
        self.tabs.add(self.tab_sort, text="Simulation")
        self.tabs.add(self.tab_stats, text="Statistiques")
        self.tabs.add(self.tab_compare, text="Comparer")
        self.tabs.add(self.tab_complexity, text="Complexité")
        self.tabs.add(self.tab_challenge, text="Défis")
        self.tabs.add(self.tab_help, text="Aide")
        self._build_sort()
        self._build_stats()
        self._build_compare()
        self._build_complexity()
        self._build_challenge()
        self._build_help()
        ttk.Label(outer, textvariable=self.status, anchor="w", relief="sunken", padding=(6, 3)).pack(fill="x", pady=(7, 0))

    def _build_sort(self):
        tab = self.tab_sort
        data = ttk.LabelFrame(tab, text="Données d’entrée", padding=8)
        data.pack(fill="x", pady=(0, 7))
        ttk.Label(data, text="Profil").grid(row=0, column=0, sticky="w")
        self.profile_box = ttk.Combobox(data, textvariable=self.profile, values=PROFILS, state="readonly", width=18)
        self.profile_box.grid(row=0, column=1, padx=5)
        ttk.Label(data, text="Nombre de valeurs").grid(row=0, column=2, padx=(12, 0))
        ttk.Spinbox(data, from_=5, to=100, textvariable=self.count, width=6).grid(row=0, column=3, padx=5)
        ttk.Button(data, text="Générer", command=self.new_data).grid(row=0, column=4, padx=3)
        ttk.Label(data, text="Forme").grid(row=0, column=5, padx=(12, 0))
        self.shape_box = ttk.Combobox(data, textvariable=self.shape_mode,
                                      values=("Boules", "Rectangles"), state="readonly", width=11)
        self.shape_box.grid(row=0, column=6, padx=5)
        self.shape_box.bind("<<ComboboxSelected>>", lambda _e: self.draw_bars())
        ttk.Label(data, text="Valeurs personnalisées").grid(row=1, column=0, sticky="w", pady=(6, 0))
        self.custom_entry = ttk.Entry(data)
        self.custom_entry.grid(row=1, column=1, columnspan=3, sticky="ew", padx=5, pady=(6, 0))
        ttk.Button(data, text="Utiliser ces valeurs", command=self.use_custom).grid(row=1, column=4, padx=3, pady=(6, 0))
        data.columnconfigure(1, weight=1)

        algo = ttk.LabelFrame(tab, text="Algorithme et commandes", padding=8)
        algo.pack(fill="x", pady=(0, 7))
        self.algo_box = ttk.Combobox(algo, textvariable=self.algorithm, values=tuple(ALGOS), state="readonly", width=34)
        self.algo_box.grid(row=0, column=0, padx=(0, 8), sticky="w")
        self.algo_box.bind("<<ComboboxSelected>>", self.show_algorithm_info)
        self.algo_info = ttk.Label(algo, text="", style="Subtle.TLabel", wraplength=600)
        self.algo_info.grid(row=0, column=1, sticky="ew")
        buttons = ttk.Frame(algo)
        buttons.grid(row=1, column=0, columnspan=2, sticky="w", pady=(8, 0))
        self.btn_start = ttk.Button(buttons, text="Trier / Reprendre", command=self.start)
        self.btn_start.pack(side="left", padx=(0, 4))
        self.btn_step = ttk.Button(buttons, text="Pas à pas", command=self.step)
        self.btn_step.pack(side="left", padx=4)
        self.btn_back = ttk.Button(buttons, text="Étape précédente", command=self.step_back)
        self.btn_back.pack(side="left", padx=4)
        self.btn_stop = ttk.Button(buttons, text="Arrêter", command=self.stop)
        self.btn_stop.pack(side="left", padx=4)
        ttk.Button(buttons, text="Réinitialiser", command=self.reset).pack(side="left", padx=4)
        ttk.Button(buttons, text="Mélanger", command=self.new_data).pack(side="left", padx=4)
        ttk.Label(buttons, text="Vitesse").pack(side="left", padx=(12, 3))
        ttk.Scale(buttons, from_=1, to=100, variable=self.speed, length=130).pack(side="left")
        ttk.Checkbutton(buttons, text="Journal détaillé", variable=self.verbose).pack(side="left", padx=(12, 3))
        ttk.Checkbutton(buttons, text="Afficher les comparaisons", variable=self.show_comparisons).pack(side="left", padx=3)
        algo.columnconfigure(1, weight=1)

        self.canvas = tk.Canvas(tab, height=320, background="white", highlightthickness=1, highlightbackground="#B8C0CC")
        self.canvas.pack(fill="both", expand=True, pady=(0, 7))
        self.canvas.bind("<Configure>", lambda _e: self.draw_bars())
        self.canvas.bind("<ButtonPress-1>", self.drag_begin)
        self.canvas.bind("<B1-Motion>", self.drag_move)
        self.canvas.bind("<ButtonRelease-1>", self.drag_end)
        self.canvas.bind("<Double-Button-1>", self.edit_selected)

        log_frame = ttk.LabelFrame(tab, text="Journal des étapes", padding=5)
        log_frame.pack(fill="both", expand=False)
        self.log = ScrolledText(log_frame, height=7, wrap="word", font=("TkFixedFont", 9), state="disabled")
        self.log.pack(fill="both", expand=True)
        self.show_algorithm_info()

    def _build_stats(self):
        controls = ttk.Frame(self.tab_stats)
        controls.pack(fill="x")
        ttk.Button(controls, text="Actualiser", command=self.update_stats).pack(side="left")
        self.stat_labels = {}
        names = (("Étapes", "etapes"), ("Comparaisons", "cmp"), ("Échanges", "swap"), ("Écritures", "set"),
                 ("Valeurs déplacées", "mv"), ("Distance des échanges", "dist"), ("Temps écoulé", "time"))
        grid = ttk.Frame(self.tab_stats, padding=8)
        grid.pack(fill="x")
        for i, (label, key) in enumerate(names):
            cell = ttk.LabelFrame(grid, text=label, padding=8)
            cell.grid(row=i // 4, column=i % 4, sticky="nsew", padx=4, pady=4)
            self.stat_labels[key] = tk.StringVar(value="0")
            ttk.Label(cell, textvariable=self.stat_labels[key], font=("TkDefaultFont", 14, "bold")).pack()
            grid.columnconfigure(i % 4, weight=1)
        table_frame = ttk.Frame(self.tab_stats)
        table_frame.pack(fill="both", expand=True, pady=(8, 0))
        self.stats_table = ttk.Treeview(table_frame, columns=("position", "value", "comparisons", "moves"), show="headings", height=12)
        for col, label, width in (("position", "Position", 90), ("value", "Valeur initiale", 120),
                                  ("comparisons", "Comparaisons", 130), ("moves", "Déplacements", 100)):
            self.stats_table.heading(col, text=label)
            self.stats_table.column(col, width=width, anchor="center")
        stats_scroll = ttk.Scrollbar(table_frame, orient="vertical", command=self.stats_table.yview)
        self.stats_table.configure(yscrollcommand=stats_scroll.set)
        self.stats_table.pack(side="left", fill="both", expand=True)
        stats_scroll.pack(side="right", fill="y")

    def _build_compare(self):
        top = ttk.Frame(self.tab_compare)
        top.pack(fill="x", pady=(0, 6))
        ttk.Button(top, text="Comparer tous les algorithmes", command=self.compare).pack(side="left")
        ttk.Button(top, text="Exporter le rapport de comparaison…", command=self.export_report).pack(side="left", padx=5)
        cols = ("algorithm", "best", "average", "worst", "stable", "inplace", "comparisons", "moves", "ms")
        compare_frame = ttk.Frame(self.tab_compare)
        compare_frame.pack(fill="both", expand=True)
        self.compare_table = ttk.Treeview(compare_frame, columns=cols, show="headings", height=13)
        headers = (("algorithm", "Algorithme", 205), ("best", "Meilleur cas", 145), ("average", "Cas moyen", 145),
                   ("worst", "Pire cas", 145), ("stable", "Stable", 65), ("inplace", "En place", 70),
                   ("comparisons", "Comparaisons", 105), ("moves", "Valeurs déplacées", 100), ("ms", "Temps (ms)", 90))
        for col, title, width in headers:
            self.compare_table.heading(col, text=title)
            self.compare_table.column(col, width=width, anchor="center" if col != "algorithm" else "w")
        compare_x = ttk.Scrollbar(compare_frame, orient="horizontal", command=self.compare_table.xview)
        self.compare_table.configure(xscrollcommand=compare_x.set)
        self.compare_table.pack(fill="both", expand=True)
        compare_x.pack(fill="x")
        ttk.Separator(self.tab_compare).pack(fill="x", pady=8)
        race_box = ttk.LabelFrame(self.tab_compare, text="Course côte à côte", padding=8)
        race_box.pack(fill="both", expand=True)
        row = ttk.Frame(race_box)
        row.pack(fill="x")
        self.race_a = tk.StringVar(value=list(ALGOS)[0])
        self.race_b = tk.StringVar(value=list(ALGOS)[1])
        ttk.Combobox(row, textvariable=self.race_a, values=tuple(ALGOS), state="readonly", width=30).pack(side="left")
        ttk.Label(row, text="vs").pack(side="left", padx=5)
        ttk.Combobox(row, textvariable=self.race_b, values=tuple(ALGOS), state="readonly", width=30).pack(side="left")
        ttk.Button(row, text="Lancer la course", command=self.start_race).pack(side="left", padx=8)
        self.race_status = tk.StringVar(value="")
        ttk.Label(row, textvariable=self.race_status).pack(side="left", padx=5)
        canvases = ttk.Frame(race_box)
        canvases.pack(fill="both", expand=True, pady=(5, 0))
        self.race_canvas_a = tk.Canvas(canvases, height=120, background="white", highlightthickness=1, highlightbackground="#B8C0CC")
        self.race_canvas_b = tk.Canvas(canvases, height=120, background="white", highlightthickness=1, highlightbackground="#B8C0CC")
        self.race_canvas_a.pack(side="left", fill="both", expand=True, padx=(0, 4))
        self.race_canvas_b.pack(side="left", fill="both", expand=True, padx=(4, 0))

    def _build_complexity(self):
        controls = ttk.Frame(self.tab_complexity)
        controls.pack(fill="x")
        ttk.Label(controls, text="Algorithme").pack(side="left")
        self.bench_algo = tk.StringVar(value="Tri fusion")
        ttk.Combobox(controls, textvariable=self.bench_algo, values=tuple(ALGOS), state="readonly", width=30).pack(side="left", padx=5)
        ttk.Label(controls, text="Profil des données").pack(side="left", padx=(12, 0))
        self.bench_profile = tk.StringVar(value="Aléatoire")
        ttk.Combobox(controls, textvariable=self.bench_profile, values=PROFILS, state="readonly", width=18).pack(side="left", padx=5)
        ttk.Button(controls, text="Mesurer plusieurs tailles", command=self.run_benchmark).pack(side="left", padx=5)
        self.bench_canvas = tk.Canvas(self.tab_complexity, background="white", highlightthickness=1, highlightbackground="#B8C0CC")
        self.bench_canvas.pack(fill="both", expand=True, pady=8)
        self.bench_table = ttk.Treeview(self.tab_complexity, columns=("n", "comparisons", "moves", "ms"), show="headings", height=6)
        for col, label in (("n", "Taille du tableau"), ("comparisons", "Comparaisons"), ("moves", "Valeurs déplacées"), ("ms", "Temps (ms)")):
            self.bench_table.heading(col, text=label)
            self.bench_table.column(col, anchor="center", width=140)
        self.bench_table.pack(fill="x")

    def _build_challenge(self):
        frame = ttk.LabelFrame(self.tab_challenge, text="Défi de comparaison", padding=12)
        frame.pack(fill="x", anchor="n")
        self.challenge_text = tk.StringVar(value="Générez un défi pour commencer.")
        ttk.Label(frame, textvariable=self.challenge_text, wraplength=850).pack(anchor="w", pady=(0, 8))
        self.challenge_values_label = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.challenge_values_label, font=("TkFixedFont", 11, "bold")).pack(anchor="w", pady=4)
        row = ttk.Frame(frame)
        row.pack(anchor="w", pady=6)
        self.challenge_answer = tk.StringVar(value=list(ALGOS)[0])
        ttk.Combobox(row, textvariable=self.challenge_answer, values=tuple(ALGOS), state="readonly", width=34).pack(side="left")
        ttk.Button(row, text="Vérifier la réponse", command=self.check_challenge).pack(side="left", padx=6)
        ttk.Button(row, text="Nouveau défi", command=self.new_challenge).pack(side="left", padx=6)
        self.challenge_feedback = tk.StringVar(value="")
        ttk.Label(frame, textvariable=self.challenge_feedback, font=("TkDefaultFont", 11, "bold")).pack(anchor="w", pady=5)
        ttk.Label(frame, text="Conseil : utilisez Comparer pour examiner les mesures sur les mêmes données.", style="Subtle.TLabel").pack(anchor="w")

    def _build_help(self):
        frame = ttk.LabelFrame(self.tab_help, text="Guide de SortLab", padding=8)
        frame.pack(fill="both", expand=True)
        help_text = ScrolledText(frame, wrap="word", font=("TkDefaultFont", 10), height=18)
        help_text.pack(fill="both", expand=True)
        lines = [
            "PRISE EN MAIN\nChoisissez un profil de données ou saisissez vos propres entiers. Sélectionnez un algorithme, puis lancez l’animation, avancez pas à pas ou revenez à l’étape précédente. Vous pouvez aussi déplacer les barres à la souris avant le tri.\n",
            "PROFILS DE DONNÉES\nAléatoire, déjà trié, trié à l’envers, presque trié, avec doublons, peu de valeurs distinctes ou valeurs négatives. Ces profils permettent de comparer l’effet de la forme de l’entrée sur chaque algorithme.\n",
            "STATISTIQUES\nLes comparaisons comptent les tests entre deux valeurs. Les échanges permutent deux positions ; les écritures correspondent notamment au tri fusion, au tri par comptage et au tri radix. La distance des échanges additionne les écarts entre les positions permutées.\n",
            "PROPRIÉTÉS DES ALGORITHMES\nStable : conserve l’ordre relatif des éléments égaux. En place : trie avec une mémoire auxiliaire limitée, sans tableau de sortie proportionnel à la taille de l’entrée. Les complexités indiquées distinguent les meilleurs, moyens et pires cas lorsqu’ils sont connus.\n",
            "RACCOURCIS\nEspace : démarrer, mettre en pause ou reprendre. Flèche droite : étape suivante. Flèche gauche : étape précédente. Échap : arrêter. N : générer de nouvelles données. Ctrl+S : enregistrer une expérience.\n",
            "EXPÉRIENCES ET RAPPORTS\nEnregistrez une expérience au format JSON pour conserver le tableau, l’algorithme, le profil et la vitesse. La page Comparer exporte les mesures de tous les algorithmes en CSV.\n",
            "ALGORITHMES DISPONIBLES\n",
        ]
        for name, (complexity, summary) in ALGO_INFO.items():
            stable, inplace, cases = ALGO_PROPERTIES[name]
            lines.append(f"{name}\n{summary}\nComplexité : {complexity}. Stable : {stable}. En place : {inplace}.\n")
        help_text.insert("1.0", "\n".join(lines))
        help_text.configure(state="disabled")

    def bind_keys(self):
        self.root.bind("<space>", lambda _e: self.start())
        self.root.bind("<Right>", lambda _e: self.step())
        self.root.bind("<Left>", lambda _e: self.step_back())
        self.root.bind("<Escape>", lambda _e: self.stop())
        self.root.bind("<Key-n>", lambda _e: self.new_data())
        self.root.bind("<Control-s>", lambda _e: self.save_experiment())

    def show_algorithm_info(self, _event=None):
        name = self.algorithm.get()
        if name not in ALGO_INFO:
            return
        complexity, summary = ALGO_INFO[name]
        stable, inplace, detail = ALGO_PROPERTIES[name]
        self.algo_info.config(text=f"{summary}  Complexité : {complexity}. Stable : {stable}. En place : {inplace}.")
        self.status.set(detail)

    def generate_values(self, count, profile=None):
        profile = profile or self.profile.get()
        count = max(5, min(5000, int(count)))
        base = list(range(1, count + 1))
        if profile == "Déjà trié":
            return base
        if profile == "Trié à l’envers":
            return base[::-1]
        if profile == "Presque trié":
            values = base[:]
            for _ in range(max(1, count // 12)):
                i, j = random.randrange(count), random.randrange(count)
                values[i], values[j] = values[j], values[i]
            return values
        if profile == "Avec doublons":
            return [random.randint(1, max(2, count // 4)) for _ in range(count)]
        if profile == "Peu de valeurs distinctes":
            return [random.randint(1, 5) for _ in range(count)]
        if profile == "Valeurs négatives":
            return [random.randint(-count, count) for _ in range(count)]
        random.shuffle(base)
        return base

    def new_data(self):
        self.stop()
        try:
            self.count.set(max(5, min(100, int(self.count.get()))))
        except (ValueError, tk.TclError):
            self.count.set(30)
        self.values = self.generate_values(self.count.get())
        self.initial = self.values[:]
        self._reset_run()
        self.draw_bars()
        self.status.set(f"Généré : {len(self.values)} valeurs, profil {self.profile.get().lower()}.")

    def use_custom(self):
        try:
            values = [int(part) for part in self.custom_entry.get().replace(",", " ").split()]
            if not 5 <= len(values) <= 100:
                raise ValueError("Saisissez entre 5 et 100 entiers.")
        except ValueError as exc:
            messagebox.showerror("Saisie invalide", str(exc) or "Saisissez des entiers séparés par des espaces ou des virgules.")
            return
        self.stop()
        self.values = values
        self.initial = values[:]
        self.count.set(len(values))
        self.profile.set("Valeurs personnalisées")
        self._reset_run()
        self.draw_bars()

    def _reset_run(self):
        self.values = self.initial[:]
        self.stats = Stats(len(self.values))
        self.gen = None
        self.running = self.paused = False
        self.history = []
        self.last_indices = ()
        self.last_op = None
        self.elapsed = 0.0
        self._update_all()

    def reset(self):
        self.stop()
        self._reset_run()
        self.draw_bars()

    def draw_bars(self, canvas=None, values=None, highlight=(), title=None):
        canvas = canvas or self.canvas
        values = self.values if values is None else values
        canvas.delete("all")
        w, h = max(canvas.winfo_width(), 200), max(canvas.winfo_height(), 100)
        margin, top, bottom = 24, (30 if title else 18), 28
        if title:
            canvas.create_text(10, 8, anchor="nw", text=title, font=("TkDefaultFont", 9, "bold"))
        n = len(values)
        if not n:
            return
        lo, hi = min(values), max(values)
        span = max(1, hi - lo)
        slot = (w - 2 * margin) / n
        usable = max(36, h - top - bottom)
        max_d = max(8, min(slot * .94, usable * .90, 112))
        baseline = h - bottom

        def blend(first, second, amount):
            a = tuple(int(first[i:i + 2], 16) for i in (1, 3, 5))
            b = tuple(int(second[i:i + 2], 16) for i in (1, 3, 5))
            return "#" + "".join(f"{round(a[k] + (b[k] - a[k]) * amount):02x}" for k in range(3))

        for i, value in enumerate(values):
            fraction = (value - lo) / span
            active = i in highlight and canvas is self.canvas
            color = ("#DC2626" if self.last_op == "cmp" else "#D97706") if active else blend("#2563EB", "#0F9F9A", fraction)
            cx = margin + (i + .5) * slot

            if self.shape_mode.get() == "Boules":
                diameter = max(8, max_d * (.48 + .52 * fraction))
                radius = diameter / 2
                cy = baseline - radius - 5
                # Soft contact shadow, shaded body, and two specular highlights
                # create a polished sphere without external image assets.
                canvas.create_oval(cx - radius * .78 + 2, baseline - 8,
                                   cx + radius * .78 + 3, baseline - 1,
                                   fill="#D7DEE8", outline="")
                canvas.create_oval(cx - radius, cy - radius, cx + radius, cy + radius,
                                   fill=blend(color, "#102A56", .48), outline="#173B70", width=1)
                inset = max(1, radius * .09)
                canvas.create_oval(cx - radius + inset, cy - radius + inset,
                                   cx + radius - inset, cy + radius - inset,
                                   fill=color, outline="")
                shade_top = cy + radius * .32
                canvas.create_oval(cx - radius * .78, shade_top,
                                   cx + radius * .78, cy + radius * .82,
                                   fill=blend(color, "#102A56", .34), outline="")
                if diameter >= 12:
                    gloss = blend(color, "#FFFFFF", .68)
                    canvas.create_oval(cx - radius * .62, cy - radius * .62,
                                       cx - radius * .02, cy - radius * .28,
                                       fill=gloss, outline="")
                    canvas.create_oval(cx - radius * .49, cy - radius * .57,
                                       cx - radius * .28, cy - radius * .43,
                                       fill="#FFFFFF", outline="")
                if n <= 35 and diameter >= 20:
                    canvas.create_text(cx, cy + 1, text=str(value),
                                       font=("TkDefaultFont", max(7, min(10, int(diameter * .28))), "bold"),
                                       fill="#FFFFFF")
            else:
                bar_w = max(2, min(30, slot * .76))
                bar_h = 8 + fraction * max(8, usable - 18)
                x0 = cx - bar_w / 2
                y0 = baseline - bar_h
                canvas.create_rectangle(x0 + 2, y0 + 3, x0 + bar_w + 2, baseline + 1,
                                        fill="#D7DEE8", outline="")
                canvas.create_rectangle(x0, y0, x0 + bar_w, baseline,
                                        fill=blend(color, "#102A56", .16), outline="#1E40AF", width=1)
                if bar_w >= 6:
                    canvas.create_line(x0 + 2, y0 + 2, x0 + bar_w - 2, y0 + 2,
                                       fill=blend(color, "#FFFFFF", .58), width=1)
                if n <= 35:
                    canvas.create_text(cx, y0 - 8, text=str(value), font=("TkDefaultFont", 8))

    def _index_at(self, x, canvas=None, n=None):
        canvas = canvas or self.canvas
        n = n or len(self.values)
        if not n:
            return None
        margin = 24
        slot = (max(canvas.winfo_width(), 200) - 2 * margin) / n
        idx = int((x - margin) / slot)
        return idx if 0 <= idx < n else None

    def drag_begin(self, event):
        if self.running:
            return
        self.drag_index = self._index_at(event.x)

    def drag_move(self, event):
        if self.drag_index is None:
            return
        target = self._index_at(event.x)
        if target is not None and target != self.drag_index:
            value = self.values.pop(self.drag_index)
            self.values.insert(target, value)
            self.drag_index = target
            self.draw_bars()

    def drag_end(self, _event):
        if self.drag_index is not None:
            self.initial = self.values[:]
            self._reset_run()
            self.draw_bars()
        self.drag_index = None

    def edit_selected(self, event):
        idx = self._index_at(event.x)
        if idx is not None:
            self.custom_entry.delete(0, "end")
            self.custom_entry.insert(0, ", ".join(map(str, self.values)))
            self.custom_entry.focus_set()
            self.status.set("Modifiez les valeurs ci-dessus, puis cliquez sur « Utiliser ces valeurs ».")

    def log_line(self, text):
        self.log.configure(state="normal")
        self.log.insert("end", text + "\n")
        self.log.see("end")
        self.log.configure(state="disabled")

    def start(self):
        if self.running and self.paused:
            self.paused = False
            self.start_time = time.perf_counter()
            self.timer = None
            self._tick()
            return
        if self.running:
            if not self.paused:
                self.elapsed += time.perf_counter() - self.start_time
            self.paused = True
            if self.timer is not None:
                try:
                    self.root.after_cancel(self.timer)
                except tk.TclError:
                    pass
                self.timer = None
            self.status.set("En pause. Cliquez sur « Trier / Reprendre » pour continuer.")
            return
        self._reset_run()
        self.running = True
        self.gen = ALGOS[self.algorithm.get()](self.values)
        self.start_time = time.perf_counter()
        self.log_line(f"Début : {self.algorithm.get()} sur {len(self.values)} valeurs.")
        self._tick()

    def step(self):
        if self.running and not self.paused:
            self.elapsed += time.perf_counter() - self.start_time
            if self.timer is not None:
                try:
                    self.root.after_cancel(self.timer)
                except tk.TclError:
                    pass
                self.timer = None
        if not self.running:
            self._reset_run()
            self.running = True
            self.paused = True
            self.start_time = time.perf_counter()
            self.gen = ALGOS[self.algorithm.get()](self.values)
            self.log_line(f"Mode pas à pas : {self.algorithm.get()}.")
        self.paused = True
        if not self._advance(1):
            self._finish()
        else:
            self._update_all()

    def _advance(self, count):
        done = 0
        try:
            while done < count:
                op, idx, extra = next(self.gen)
                if op == "info":
                    if idx:
                        self.last_indices, self.last_op = idx, "pivot"
                    if self.verbose.get():
                        self.log_line(str(extra))
                    continue
                self.history.append(None)
                self.last_indices, self.last_op = idx, op
                self.stats.add(op, idx)
                done += 1
                if self.verbose.get() and (self.show_comparisons.get() or op != "cmp"):
                    self.log_line(f"[{self.stats.etapes}] {decrire(op, idx, extra)}")
        except StopIteration:
            return False
        return True

    def _tick(self):
        if not self.running or self.paused:
            return
        self.timer = None
        speed = max(1, int(self.speed.get()))
        if not self._advance(max(1, speed // 10)):
            self._finish()
            return
        self._update_all()
        self.timer = self.root.after(max(1, 250 // speed), self._tick)

    def _finish(self):
        was_paused = self.paused
        self.running = self.paused = False
        self.timer = None
        if not was_paused:
            self.elapsed += time.perf_counter() - self.start_time
        self.stats.temps = self.elapsed
        self._update_all()
        self.log_line(f"Terminé : {self.stats.cmp} comparaisons, {self.stats.mv} valeurs déplacées, {self.elapsed:.3f} s.")
        self.status.set("Tri terminé.")

    def stop(self):
        if self.timer is not None:
            try:
                self.root.after_cancel(self.timer)
            except tk.TclError:
                pass
        self.timer = None
        if self.running and not self.paused:
            self.elapsed += time.perf_counter() - self.start_time
        self.running = self.paused = False
        self.gen = None

    def step_back(self):
        if not self.history:
            return
        self.stop()
        target = len(self.history) - 1
        self.values = self.initial[:]
        self.stats = Stats(len(self.values))
        self.gen = ALGOS[self.algorithm.get()](self.values)
        self.history = []
        consumed = 0
        while consumed < target:
            op, idx, extra = next(self.gen)
            if op != "info":
                self.history.append(None)
                self.stats.add(op, idx)
                consumed += 1
        self.running = True
        self.paused = True
        self.elapsed = 0.0
        self.status.set(f"Retour à l’étape {target}. Cliquez sur « Pas à pas » ou « Trier / Reprendre » pour continuer.")
        self._update_all()

    def update_stats(self):
        s = self.stats
        elapsed = self.elapsed + (time.perf_counter() - self.start_time if self.running and not self.paused else 0.0)
        values = {"etapes": s.etapes, "cmp": s.cmp, "swap": s.swap, "set": s.set, "mv": s.mv,
                  "dist": s.dist, "time": f"{elapsed:.3f} s"}
        for key, value in values.items():
            self.stat_labels[key].set(str(value))
        for item in self.stats_table.get_children():
            self.stats_table.delete(item)
        for i, value in enumerate(self.initial):
            self.stats_table.insert("", "end", values=(i + 1, value, s.pos_cmp[i] if i < len(s.pos_cmp) else 0,
                                                          s.pos_mv[i] if i < len(s.pos_mv) else 0))

    def _update_all(self):
        self.draw_bars(highlight=self.last_indices)
        if hasattr(self, "stat_labels"):
            self.update_stats()

    def compare(self):
        self.results = [(name, executer(algo, self.initial)) for name, algo in ALGOS.items()]
        for row in self.compare_table.get_children():
            self.compare_table.delete(row)
        for name, stats in self.results:
            best, avg, worst = ALGO_PROPERTIES[name][2].split(" / ") if " / " in ALGO_PROPERTIES[name][2] else (ALGO_PROPERTIES[name][2],) * 3
            self.compare_table.insert("", "end", values=(name, best, avg, worst, ALGO_PROPERTIES[name][0],
                                                              ALGO_PROPERTIES[name][1], stats.cmp, stats.mv,
                                                              f"{stats.temps * 1000:.2f}"))
        self.status.set("Comparaison terminée. Moins d’opérations ne signifie pas toujours un temps plus court.")

    def export_report(self):
        if not self.results:
            self.compare()
        path = filedialog.asksaveasfilename(defaultextension=".csv", filetypes=(("Fichier CSV", "*.csv"),),
                                            initialfile="sortlab_comparison.csv")
        if not path:
            return
        with open(path, "w", newline="", encoding="utf-8-sig") as stream:
            writer = csv.writer(stream)
            writer.writerow(("Profil", self.profile.get()))
            writer.writerow(("Nombre de valeurs", len(self.initial)))
            writer.writerow(("Données initiales", " ".join(map(str, self.initial))))
            writer.writerow(())
            writer.writerow(("Algorithme", "Meilleur cas", "Cas moyen", "Pire cas", "Stable", "En place", "Comparaisons", "Échanges", "Écritures", "Valeurs déplacées", "Distance des échanges", "Temps (ms)"))
            for name, stats in self.results:
                props = ALGO_PROPERTIES[name]
                complexity = props[2].split(" / ") if " / " in props[2] else [props[2]] * 3
                writer.writerow((name, *complexity, props[0], props[1], stats.cmp, stats.swap, stats.set,
                                 stats.mv, stats.dist, f"{stats.temps * 1000:.3f}"))
        self.status.set(f"Rapport enregistré dans {path}")

    def run_benchmark(self):
        algo_name, profile = self.bench_algo.get(), self.bench_profile.get()
        sizes = (16, 32, 64, 128, 256)
        self.benchmarks = []
        for n in sizes:
            values = self.generate_values(n, profile)
            stats = executer(ALGOS[algo_name], values)
            self.benchmarks.append((n, stats))
        for row in self.bench_table.get_children():
            self.bench_table.delete(row)
        for n, s in self.benchmarks:
            self.bench_table.insert("", "end", values=(n, s.cmp, s.mv, f"{s.temps * 1000:.3f}"))
        self.draw_benchmark(algo_name)

    def draw_benchmark(self, algo_name):
        c = self.bench_canvas
        c.delete("all")
        w, h = max(c.winfo_width(), 300), max(c.winfo_height(), 200)
        left, right, top, bottom = 58, 18, 28, 62
        c.create_text(left, 8, anchor="nw", text=f"Comparaisons mesurées et croissance théorique — {algo_name}", font=("TkDefaultFont", 10, "bold"))
        if not self.benchmarks:
            return
        measured = [s.cmp for _, s in self.benchmarks]
        base = max(1, measured[0])
        n0 = max(1, self.benchmarks[0][0])
        families = {
            "Mesuré": measured,
            "Repère O(n)": [base * n / n0 for n, _ in self.benchmarks],
            "Repère O(n log n)": [base * n * max(1, math.log2(n)) / (n0 * max(1, math.log2(n0))) for n, _ in self.benchmarks],
            "Repère O(n²)": [base * (n / n0) ** 2 for n, _ in self.benchmarks],
        }
        max_v = max([max(values) for values in families.values()] + [1])
        plot_w, plot_h = w - left - right, h - top - bottom
        for step in range(5):
            y = top + plot_h * step / 4
            c.create_line(left, y, w - right, y, fill="#E5E7EB")
            c.create_text(left - 6, y, text=str(round(max_v * (4 - step) / 4)), anchor="e", font=("TkDefaultFont", 8))
        colors = ("#2563EB", "#16A34A", "#D97706", "#9333EA")
        for series_index, (label, values) in enumerate(families.items()):
            points = []
            for i, value in enumerate(values):
                x = left + plot_w * i / max(1, len(values) - 1)
                y = top + plot_h * (1 - value / max_v)
                points.extend((x, y))
                if series_index == 0:
                    c.create_text(x, h - bottom + 8, text=str(self.benchmarks[i][0]), font=("TkDefaultFont", 8))
            color = colors[series_index]
            if len(points) >= 4:
                c.create_line(*points, fill=color, width=2 if series_index == 0 else 1, dash=() if series_index == 0 else (4, 3))
            for i in range(0, len(points), 2):
                c.create_oval(points[i] - 3, points[i + 1] - 3, points[i] + 3, points[i + 1] + 3, fill=color, outline="")
            lx = left + series_index * 145
            c.create_line(lx, h - 8, lx + 18, h - 8, fill=color, width=2, dash=() if series_index == 0 else (4, 3))
            c.create_text(lx + 23, h - 8, text=label, anchor="w", font=("TkDefaultFont", 8))
        c.create_text(left, h - 34, anchor="w", text="Taille du tableau · axe vertical : comparaisons", font=("TkDefaultFont", 8), fill="#555555")

    def new_challenge(self):
        self.challenge_values = self.generate_values(random.randint(8, 16), random.choice(PROFILS[:-1]))
        self.challenge_values_label.set("Données : " + ", ".join(map(str, self.challenge_values)))
        self.challenge_text.set("Choisissez l’algorithme qui effectue le moins de comparaisons sur ces données. Les égalités sont acceptées.")
        self.challenge_feedback.set("")

    def check_challenge(self):
        if not self.challenge_values:
            self.new_challenge()
        counts = {name: executer(algo, self.challenge_values).cmp for name, algo in ALGOS.items()}
        minimum = min(counts.values())
        winners = [name for name, value in counts.items() if value == minimum]
        answer = self.challenge_answer.get()
        if answer in winners:
            self.challenge_feedback.set(f"Bonne réponse ! {answer} a effectué {minimum} comparaisons. Autres meilleurs choix : {', '.join(winners)}.")
        else:
            self.challenge_feedback.set(f"Pas cette fois. {', '.join(winners)} a effectué le moins de comparaisons ({minimum}).")

    def save_experiment(self):
        path = filedialog.asksaveasfilename(defaultextension=".json", filetypes=(("Expérience SortLab", "*.json"),),
                                            initialfile="sortlab_experiment.json")
        if not path:
            return
        data = {"format": "SortLab", "version": 1, "values": self.initial, "algorithm": self.algorithm.get(),
                "pattern": self.profile.get(), "speed": int(self.speed.get()),
                "shape": self.shape_mode.get()}
        with open(path, "w", encoding="utf-8") as stream:
            json.dump(data, stream, ensure_ascii=False, indent=2)
        self.status.set(f"Expérience enregistrée dans {path}")

    def open_experiment(self):
        path = filedialog.askopenfilename(filetypes=(("Expérience SortLab", "*.json"), ("Fichiers JSON", "*.json")))
        if not path:
            return
        try:
            with open(path, encoding="utf-8") as stream:
                data = json.load(stream)
            values = [int(value) for value in data["values"]]
            if not 5 <= len(values) <= 100 or data.get("format") != "SortLab":
                raise ValueError("Format d’expérience ou nombre de valeurs non pris en charge.")
            algorithm = data.get("algorithm", list(ALGOS)[0])
            if algorithm not in ALGOS:
                raise ValueError("L’algorithme enregistré n’est pas disponible.")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as exc:
            messagebox.showerror("Impossible d’ouvrir l’expérience", str(exc))
            return
        self.stop()
        self.values = values[:]
        self.initial = values[:]
        self.count.set(len(values))
        self.algorithm.set(algorithm)
        self.profile.set(data.get("pattern", "Valeurs personnalisées"))
        self.speed.set(data.get("speed", 50))
        shape = data.get("shape", "Boules")
        self.shape_mode.set(shape if shape in ("Boules", "Rectangles") else "Boules")
        self._reset_run()
        self.show_algorithm_info()
        self.draw_bars()
        self.status.set(f"Expérience ouverte : {path}")

    def start_race(self):
        if self.race_timer is not None:
            self.root.after_cancel(self.race_timer)
            self.race_timer = None
        self.race = {
            "a": {"name": self.race_a.get(), "values": self.initial[:], "gen": None, "stats": Stats(len(self.initial)), "done": False},
            "b": {"name": self.race_b.get(), "values": self.initial[:], "gen": None, "stats": Stats(len(self.initial)), "done": False},
        }
        for side in ("a", "b"):
            run = self.race[side]
            run["gen"] = ALGOS[run["name"]](run["values"])
        self._race_tick()

    def _race_tick(self):
        if not self.race:
            return
        self.race_timer = None
        speed = max(1, int(self.speed.get()))
        for side, canvas in (("a", self.race_canvas_a), ("b", self.race_canvas_b)):
            run = self.race[side]
            for _ in range(max(1, speed // 12)):
                if run["done"]:
                    break
                try:
                    op, idx, extra = next(run["gen"])
                    if op != "info":
                        run["stats"].add(op, idx)
                except StopIteration:
                    run["done"] = True
            self.draw_bars(canvas, run["values"], title=f"{run['name']} — {run['stats'].cmp} comparaisons")
        a, b = self.race["a"], self.race["b"]
        if a["done"] and b["done"]:
            self.race_status.set(f"Terminé — {a['stats'].cmp} contre {b['stats'].cmp} comparaisons")
        else:
            self.race_status.set("Course en cours…")
            self.race_timer = self.root.after(max(1, 250 // speed), self._race_tick)


def main():
    root = tk.Tk()
    App(root)
    root.mainloop()


if __name__ == "__main__":
    main()
