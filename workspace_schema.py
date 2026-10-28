"""Validation des outils optionnels, toujours rattachés à la boutique connectée."""
import re
from datetime import date

def validate_workspace(w):
    if w is None:
        return
    def text(v, limit=200):
        return isinstance(v, str) and len(v) <= limit
    def number(v):
        return type(v) is int and 0 <= v <= 10**12
    def iso(v):
        try:
            return isinstance(v, str) and date.fromisoformat(v).isoformat() == v
        except ValueError:
            return False
    if not isinstance(w, dict):
        raise ValueError('Espace outils invalide.')
    modules = w.get('modules', {})
    if not isinstance(modules, dict) or any(type(v) is not bool for v in modules.values()):
        raise ValueError('Configuration des modules invalide.')
    d = w.get('documents', {})
    if not isinstance(d, dict):
        raise ValueError('Modèle de document invalide.')
    for key, maximum in [('title', 70), ('subtitle', 160), ('footer', 400)]:
        if not text(d.get(key, ''), maximum):
            raise ValueError('Texte du document trop long.')
    if d.get('format', 'a4') not in ('a4', '80') or not re.fullmatch(r'#[0-9a-fA-F]{6}', d.get('color', '#17654f')):
        raise ValueError('Format ou couleur du document invalide.')
    for key in ('showPhone', 'showAddress', 'showCustomer'):
        if key in d and type(d[key]) is not bool:
            raise ValueError('Option de document invalide.')
    logo = d.get('logo', '')
    if not text(logo, 350000) or (logo and not re.fullmatch(r'data:image/(png|jpeg|webp);base64,[A-Za-z0-9+/=]+', logo)):
        raise ValueError('Logo invalide : PNG, JPEG ou WebP embarqué uniquement.')
    journal = w.get('journal', [])
    if not isinstance(journal, list) or len(journal) > 10000:
        raise ValueError('Journal trop volumineux.')
    seen = set()
    for e in journal:
        if not isinstance(e, dict) or not text(e.get('id'), 100) or not e['id'] or e['id'] in seen or not iso(e.get('date')) or not text(e.get('label'), 200) or not e['label'].strip() or not text(e.get('reference', ''), 100):
            raise ValueError('Écriture comptable invalide.')
        seen.add(e['id'])
        lines = e.get('lines')
        if not isinstance(lines, list) or not 2 <= len(lines) <= 30:
            raise ValueError('Une écriture doit contenir entre 2 et 30 lignes.')
        debit, credit = 0, 0
        for line in lines:
            if not isinstance(line, dict) or not isinstance(line.get('account'), str) or not re.fullmatch(r'[1-9][0-9]{1,9}', line['account']) or not text(line.get('label', ''), 100) or not number(line.get('debit')) or not number(line.get('credit')) or bool(line['debit']) == bool(line['credit']):
                raise ValueError('Ligne comptable invalide : un débit ou un crédit positif par ligne.')
            debit += line['debit']
            credit += line['credit']
        if debit != credit or not 0 < debit <= 10**12:
            raise ValueError('Écriture déséquilibrée : débit et crédit doivent être égaux et positifs.')
    tools = w.get('tools', [])
    if not isinstance(tools, list) or len(tools) > 30:
        raise ValueError('Maximum 30 outils personnalisés.')
    seen = set()
    for tool in tools:
        if not isinstance(tool, dict) or not text(tool.get('id'), 100) or not tool['id'] or tool['id'] in seen or not text(tool.get('name'), 70) or not tool['name'].strip() or not text(tool.get('description', ''), 250):
            raise ValueError('Outil invalide.')
        seen.add(tool['id'])
        fields, rows = tool.get('fields'), tool.get('rows')
        if not isinstance(fields, list) or not 1 <= len(fields) <= 8 or not isinstance(rows, list) or len(rows) > 10000:
            raise ValueError('Un outil doit avoir de 1 à 8 colonnes et au maximum 10 000 lignes.')
        fids = set()
        for f in fields:
            if not isinstance(f, dict) or not text(f.get('id'), 100) or not f['id'] or f['id'] in fids or not text(f.get('label'), 50) or not f['label'].strip() or f.get('type') not in ('text', 'number', 'date', 'status'):
                raise ValueError('Colonne personnalisée invalide.')
            fids.add(f['id'])
        rids = set()
        for row in rows:
            if not isinstance(row, dict) or not text(row.get('id'), 100) or not row['id'] or row['id'] in rids or not isinstance(row.get('values'), dict) or set(row['values']) != fids:
                raise ValueError('Ligne de suivi invalide.')
            rids.add(row['id'])
            for f in fields:
                value = row['values'][f['id']]
                if not text(value, 500):
                    raise ValueError('Valeur de suivi invalide.')
                if value and f['type'] == 'date' and not iso(value):
                    raise ValueError('Date de suivi invalide.')
                if value and f['type'] == 'status' and value not in ('À faire', 'En cours', 'Terminé'):
                    raise ValueError('Statut de suivi invalide.')
                if value and f['type'] == 'number' and (len(value) > 30 or not re.fullmatch(r'-?[0-9]+(?:\.[0-9]+)?', value)):
                    raise ValueError('Nombre de suivi invalide.')
