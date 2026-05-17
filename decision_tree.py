from __future__ import annotationssim
import math
from collections import Counter

class ID3Tree:

    def __init__(self, max_depth: int | None = None, min_samples_split: int = 2):
        self.max_depth         = max_depth
        self.min_samples_split = min_samples_split
        self.tree              = None          # raiz da árvore (dict ou label)
        self.attributes        = None          # nomes dos atributos
        self.continuous_attrs  = set()         # índices de atributos contínuos

    # ── Treino ─────────────────────────────────────────────────────────────

    def fit(self, data: list, labels: list,
            attribute_names: list | None = None,
            continuous_attrs: set | None = None) -> 'ID3Tree':

        n_attrs = len(data[0]) if data else 0
        self.attributes       = attribute_names or [f'attr_{i}' for i in range(n_attrs)]
        self.continuous_attrs = continuous_attrs or set()
        self.tree = self._build(data, labels, list(range(n_attrs)), depth=0)
        return self


    def predict_one(self, example: list) -> object:
        """Classifica um único exemplo percorrendo a árvore."""
        return self._traverse(self.tree, example)

    def predict(self, data: list) -> list:
        """Classifica uma lista de exemplos."""
        return [self.predict_one(row) for row in data]

    # ── Métricas ────────────────────────────────────────────────────────────

    @staticmethod
    def accuracy(y_true: list, y_pred: list) -> float:
        """Fraction of correctly classified examples."""
        if not y_true:
            return 0.0
        return sum(a == b for a, b in zip(y_true, y_pred)) / len(y_true)

    @staticmethod
    def precision_recall_f1(y_true: list, y_pred: list) -> tuple[float, float, float]:
        """
        Precision, recall e F1-score com média macro entre classes.
        Retorna (precision, recall, f1).
        """
        classes = sorted(set(y_true) | set(y_pred))
        precs, recs = [], []
        for cls in classes:
            tp = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p == cls)
            fp = sum(1 for t, p in zip(y_true, y_pred) if t != cls and p == cls)
            fn = sum(1 for t, p in zip(y_true, y_pred) if t == cls and p != cls)
            precs.append(tp / (tp + fp) if (tp + fp) > 0 else 0.0)
            recs.append( tp / (tp + fn) if (tp + fn) > 0 else 0.0)
        prec = sum(precs) / len(precs) if precs else 0.0
        rec  = sum(recs)  / len(recs)  if recs  else 0.0
        f1   = 2 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
        return prec, rec, f1

    @staticmethod
    def confusion_matrix(y_true: list, y_pred: list) -> dict:
        """
        Devolve uma matriz de confusão como dict aninhado:
            confusion_matrix[true_class][pred_class] = count
        """
        classes = sorted(set(y_true) | set(y_pred))
        cm = {c: {c2: 0 for c2 in classes} for c in classes}
        for t, p in zip(y_true, y_pred):
            cm[t][p] += 1
        return cm

    # ── Informação sobre a árvore ───────────────────────────────────────────

    def count_nodes(self) -> int:
        """Conta o total de nós (internos + folhas) na árvore."""
        return self._count_nodes(self.tree)

    def depth(self) -> int:
        """Profundidade real da árvore (0 = apenas raiz/folha)."""
        return self._tree_depth(self.tree)

    # alias para compatibilidade com código que usa `get_depth()`
    get_depth = depth

    # ── Visualização ────────────────────────────────────────────────────────

    def print_tree(self, max_levels: int | None = None,
                   max_depth: int | None = None) -> None:
        """
        Imprime a árvore de forma legível no terminal.

        max_levels e max_depth são aliases (qualquer um pode ser passado).
        """
        limit = max_depth if max_depth is not None else max_levels
        self._print_node(self.tree, indent=0, branch_label='', max_levels=limit)

    # ── Internos — construção ───────────────────────────────────────────────

    def _build(self, data: list, labels: list,
               available_attrs: list, depth: int) -> object:
        """Construção recursiva da árvore (devolve dict ou label-folha)."""

        # ── Casos base ──────────────────────────────────────────────────────
        majority = Counter(labels).most_common(1)[0][0]

        if len(set(labels)) == 1:
            return labels[0]

        if (not available_attrs
                or (self.max_depth is not None and depth >= self.max_depth)
                or len(data) < self.min_samples_split):
            return majority

        # ── Escolher o melhor atributo ──────────────────────────────────────
        best_attr, best_gain, best_threshold = None, -1.0, None

        for attr_idx in available_attrs:
            if attr_idx in self.continuous_attrs:
                gain, threshold = self._info_gain_continuous(data, labels, attr_idx)
            else:
                gain, threshold = self._info_gain_categorical(data, labels, attr_idx)
            if gain > best_gain:
                best_gain, best_attr, best_threshold = gain, attr_idx, threshold

        if best_attr is None or best_gain <= 0:
            return majority

        attr_name = self.attributes[best_attr]

        # ── Divisão por atributo contínuo (binária) ─────────────────────────
        if best_attr in self.continuous_attrs and best_threshold is not None:
            thr     = best_threshold
            thr_str = str(round(thr, 3))
            key_le  = f'<= {thr_str}'
            key_gt  = f'> {thr_str}'

            left_idx  = [i for i, row in enumerate(data) if row[best_attr] <= thr]
            right_idx = [i for i, row in enumerate(data) if row[best_attr] >  thr]

            node = {
                '_attr':      best_attr,
                '_attr_name': attr_name,
                '_threshold': thr,
                '_type':      'continuous',
                '_default':   majority,
            }
            if left_idx:
                node[key_le] = self._build(
                    [data[i] for i in left_idx],
                    [labels[i] for i in left_idx],
                    available_attrs,   # atributo contínuo pode ser reutilizado
                    depth + 1)
            if right_idx:
                node[key_gt] = self._build(
                    [data[i] for i in right_idx],
                    [labels[i] for i in right_idx],
                    available_attrs,
                    depth + 1)
            return node

        # ── Divisão por atributo categórico ─────────────────────────────────
        values          = set(row[best_attr] for row in data)
        remaining_attrs = [a for a in available_attrs if a != best_attr]

        node = {
            '_attr':      best_attr,
            '_attr_name': attr_name,
            '_type':      'categorical',
            '_default':   majority,
        }
        for val in values:
            idx = [i for i, row in enumerate(data) if row[best_attr] == val]
            if idx:
                node[val] = self._build(
                    [data[i] for i in idx],
                    [labels[i] for i in idx],
                    remaining_attrs,
                    depth + 1)
            else:
                node[val] = majority
        return node

    # ── Internos — predição ─────────────────────────────────────────────────

    def _traverse(self, node: object, example: list) -> object:
        if not isinstance(node, dict):
            return node

        attr_idx = node['_attr']
        val      = example[attr_idx]

        if node['_type'] == 'continuous':
            thr     = node['_threshold']
            thr_str = str(round(thr, 3))
            key     = f'<= {thr_str}' if val <= thr else f'> {thr_str}'
        else:
            key = val

        child = node.get(key)
        if child is None:
            return node.get('_default')
        return self._traverse(child, example)

    # ── Internos — ganho de informação ─────────────────────────────────────

    @staticmethod
    def _entropy(labels: list) -> float:
        n = len(labels)
        if n == 0:
            return 0.0
        counts = Counter(labels)
        return -sum((c / n) * math.log2(c / n) for c in counts.values() if c > 0)

    def _info_gain_categorical(self, data: list, labels: list,
                               attr_idx: int) -> tuple[float, object]:
        parent_H  = self._entropy(labels)
        values    = set(row[attr_idx] for row in data)
        cond_H    = 0.0
        for val in values:
            sub = [labels[i] for i, row in enumerate(data) if row[attr_idx] == val]
            cond_H += (len(sub) / len(labels)) * self._entropy(sub)
        return parent_H - cond_H, None

    def _info_gain_continuous(self, data: list, labels: list,
                              attr_idx: int) -> tuple[float, object]:
        """
        Avalia todos os limiares possíveis (pontos médios entre valores
        consecutivos) e devolve o que maximiza o ganho de informação.
        """
        parent_H = self._entropy(labels)
        vals     = sorted(set(row[attr_idx] for row in data))
        if len(vals) <= 1:
            return -1.0, None

        best_gain, best_thr = -1.0, None
        n = len(labels)

        for k in range(len(vals) - 1):
            thr   = (vals[k] + vals[k + 1]) / 2.0
            left  = [labels[i] for i, row in enumerate(data) if row[attr_idx] <= thr]
            right = [labels[i] for i, row in enumerate(data) if row[attr_idx] >  thr]
            if not left or not right:
                continue
            cond_H = (len(left) / n) * self._entropy(left) + \
                     (len(right) / n) * self._entropy(right)
            gain   = parent_H - cond_H
            if gain > best_gain:
                best_gain, best_thr = gain, thr

        return best_gain, best_thr

    # ── Internos — utilitários ──────────────────────────────────────────────

    @staticmethod
    def _is_meta_key(key) -> bool:
        return isinstance(key, str) and key.startswith('_')

    def _count_nodes(self, node: object) -> int:
        if not isinstance(node, dict):
            return 1
        count = 1
        for key, child in node.items():
            if not self._is_meta_key(key):
                count += self._count_nodes(child)
        return count

    def _tree_depth(self, node: object) -> int:
        if not isinstance(node, dict):
            return 0
        depths = [self._tree_depth(child)
                  for key, child in node.items()
                  if not self._is_meta_key(key)]
        return 1 + max(depths) if depths else 0

    def _print_node(self, node: object, indent: int,
                    branch_label: str, max_levels: object) -> None:
        prefix = '│   ' * max(0, indent - 1)
        connector = '├── ' if indent > 0 else ''

        if max_levels is not None and indent > max_levels:
            print(f'{prefix}{connector}{branch_label}... (truncado)')
            return

        if not isinstance(node, dict):
            print(f'{prefix}{connector}{branch_label}→ [{node}]')
            return

        attr_name = node['_attr_name']
        if node['_type'] == 'continuous':
            print(f'{prefix}{connector}{branch_label}{attr_name} ≤ / > {round(node["_threshold"], 3)}')
        else:
            print(f'{prefix}{connector}{branch_label}{attr_name}?')

        children = [(k, v) for k, v in node.items() if not self._is_meta_key(k)]
        for k, child in sorted(children, key=lambda x: str(x[0])):
            self._print_node(child, indent + 1, f'[{k}] ', max_levels)
