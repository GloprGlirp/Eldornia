"""Wirtschaft (GDD 9): Marktplatz mit Festpreis- und Auktionsangeboten, Preisvergleich, Gebühren,
Transaktionshistorie, Post und Schutzmaßnahmen gegen Duplikation und Missbrauch.

Alle Übertragungen laufen serverseitig und atomar: Ein Angebot wechselt nur dann von "active" zu "sold",
wenn es im selben Datenbankbefehl noch aktiv war – doppelte Käufe sind damit ausgeschlossen.
"""
from __future__ import annotations

import logging
import time

from sqlalchemy import and_, func, or_, select, update

from ..content.items import ITEMS, item_client_info
from ..db import SessionLocal
from ..models import Character, Mail, MarketListing, Transaction
from .entities import GameObj, Npc, Player, now

log = logging.getLogger("eldornia.market")

DEPOSIT_PCT = 0.05            # Einstellgebühr (vom Händlerpreis, pro 12 Std.)
SALE_FEE = 0.05               # Gebühr für abgeschlossene Geschäfte
MAX_LISTINGS = 40
DURATIONS = {12: 1, 24: 2, 48: 4}
MARKET_ACTIONS_PER_MIN = 30
MAIL_COST = 30
MAIL_MAX_ITEMS = 6
CATEGORIES = {"waffe": "Waffen", "ruestung": "Rüstung", "schmuck": "Schmuck", "verbrauch": "Verbrauchsgüter",
              "material": "Materialien", "rezept": "Rezepte", "sonstiges": "Sonstiges"}


def item_category(it: dict) -> str:
    t = it["type"]
    if t == "weapon" or (t == "armor" and it.get("slot") == "off_hand" and it.get("sub") in ("schild",)):
        return "waffe" if t == "weapon" else "ruestung"
    if t == "armor":
        return "ruestung"
    if t == "jewelry":
        return "schmuck"
    if t == "consumable":
        if (it.get("use") or {}).get("type") == "learn_recipe":
            return "rezept"
        return "verbrauch"
    if t == "material":
        return "material"
    return "sonstiges"


class EconomyMixin:
    def _rate_ok(self, p: Player) -> bool:
        t = now()
        lst = [x for x in p.misc.get("_market_t", []) if t - x < 60]
        if len(lst) >= MARKET_ACTIONS_PER_MIN:
            self.err(p, "Zu viele Marktaktionen. Wartet einen Moment.")
            return False
        lst.append(t)
        p.misc["_market_t"] = lst
        return True

    def near_market(self, p: Player) -> bool:
        for e in p.zone.entities.values():
            if isinstance(e, Npc) and "auction" in e.tpl.get("services", []) and p.dist(e) < 9:
                return True
        return False

    # ================================================================== Suche & Übersicht
    def market_search(self, p: Player, m: dict):
        if not self.near_market(p):
            self.err(p, "Sprecht mit einem Auktionator.")
            return
        q = str(m.get("q", "")).strip()[:40]
        cat = m.get("cat")
        rar = m.get("rarity")
        lmin, lmax = int(m.get("lmin") or 0), int(m.get("lmax") or 99)
        stat, smin = m.get("stat"), m.get("smin")
        page = max(0, int(m.get("page", 0) or 0))
        sort = m.get("sort", "price")
        with SessionLocal() as s:
            st = select(MarketListing).where(MarketListing.status == "active", MarketListing.expires_at > time.time())
            if q:
                st = st.where(MarketListing.item_name.ilike(f"%{q}%"))
            if cat in CATEGORIES:
                st = st.where(MarketListing.category == cat)
            if isinstance(rar, int) and 0 <= rar <= 6:
                st = st.where(MarketListing.rarity >= rar)
            st = st.where(MarketListing.level >= lmin, MarketListing.level <= lmax)
            order = {"price": MarketListing.price / MarketListing.quantity, "level": MarketListing.level.desc(),
                     "new": MarketListing.id.desc(), "rarity": MarketListing.rarity.desc()}.get(sort, MarketListing.price)
            rows = s.execute(st.order_by(order).limit(400)).scalars().all()
        if stat and smin:
            try:
                smin_v = float(smin)
                rows = [r for r in rows if ITEMS.get(r.item_id, {}).get("stats", {}).get(stat, 0) >= smin_v]
            except ValueError:
                pass
        total = len(rows)
        rows = rows[page * 50:(page + 1) * 50]
        self.send(p, {"t": "market", "list": [self._listing(r, p) for r in rows], "total": total, "page": page,
                      "items": self.item_info_for(p, [r.item_id for r in rows]), "cats": CATEGORIES})

    def _listing(self, r: MarketListing, p: Player) -> dict:
        return {"id": r.id, "i": r.item_id, "n": r.quantity, "price": r.price, "bid": r.bid, "start_bid": r.start_bid,
                "seller": r.seller_name, "mine": r.seller_id == p.char_id, "left": int(r.expires_at - time.time()),
                "top_bidder": r.bidder_id == p.char_id, "extra": r.extra or {}}

    def market_price_info(self, p: Player, item_id: str):
        """Preisvergleich ähnlicher Gegenstände (aktive Angebote und letzte Verkäufe)."""
        if item_id not in ITEMS:
            return
        with SessionLocal() as s:
            act = s.execute(select(func.min(MarketListing.price * 1.0 / MarketListing.quantity),
                                   func.avg(MarketListing.price * 1.0 / MarketListing.quantity), func.count())
                            .where(MarketListing.item_id == item_id, MarketListing.status == "active")).one()
            sold = s.execute(select(func.avg(Transaction.price * 1.0 / Transaction.quantity), func.count())
                             .where(Transaction.item_id == item_id, Transaction.kind == "market")).one()
        it = ITEMS[item_id]
        self.send(p, {"t": "market_price", "i": item_id, "min": int(act[0] or 0), "avg": int(act[1] or 0), "count": act[2],
                      "sold_avg": int(sold[0] or 0), "sold_count": sold[1], "vendor": it.get("sell", 0)})

    def market_mine(self, p: Player):
        with SessionLocal() as s:
            rows = s.execute(select(MarketListing).where(MarketListing.seller_id == p.char_id, MarketListing.status == "active")
                             .order_by(MarketListing.id.desc())).scalars().all()
            bids = s.execute(select(MarketListing).where(MarketListing.bidder_id == p.char_id, MarketListing.status == "active")).scalars().all()
            hist = s.execute(select(Transaction).where(Transaction.kind == "market",
                                                       or_(Transaction.buyer_id == p.char_id, Transaction.seller_id == p.char_id))
                             .order_by(Transaction.id.desc()).limit(40)).scalars().all()
        self.send(p, {"t": "market_mine", "list": [self._listing(r, p) for r in rows], "bids": [self._listing(r, p) for r in bids],
                      "history": [{"i": h.item_id, "n": h.quantity, "price": h.price, "fee": h.fee,
                                   "sold": h.seller_id == p.char_id, "t": h.created_at.timestamp() if h.created_at else 0} for h in hist],
                      "items": self.item_info_for(p, [r.item_id for r in rows + bids] + [h.item_id for h in hist if h.item_id])})

    # ================================================================== Einstellen
    def market_post(self, p: Player, m: dict):
        if not self.near_market(p) or not self._rate_ok(p):
            return
        slot = m.get("slot")
        if not isinstance(slot, int) or not (0 <= slot < len(p.bags)) or not p.bags[slot]:
            return
        inst = p.bags[slot]
        it = ITEMS[inst["i"]]
        if inst.get("b") or it.get("quest") or it.get("bind") == "bop":
            self.err(p, "Gebundene Gegenstände können nicht verkauft werden.")
            return
        try:
            price = int(m.get("price", 0))
            start = int(m.get("bid", 0) or 0)
            hours = int(m.get("hours", 24))
        except (TypeError, ValueError):
            return
        if hours not in DURATIONS:
            hours = 24
        if price <= 0 or price > 10_000_000_000 or start < 0 or (start and start > price):
            self.err(p, "Ungültiger Preis.")
            return
        deposit = max(1, int(it.get("sell", 1) * inst["n"] * DEPOSIT_PCT * DURATIONS[hours]))
        if p.copper < deposit:
            self.err(p, f"Die Einstellgebühr beträgt {self.fmt_money(deposit)}.")
            return
        with SessionLocal() as s:
            cnt = s.execute(select(func.count()).where(MarketListing.seller_id == p.char_id, MarketListing.status == "active")).scalar()
            if cnt >= MAX_LISTINGS:
                self.err(p, f"Ihr habt bereits {MAX_LISTINGS} Angebote.")
                return
            p.bags[slot] = None
            p.copper -= deposit
            s.add(MarketListing(seller_id=p.char_id, seller_name=p.name, item_id=inst["i"], item_name=it["name"],
                                category=item_category(it), rarity=it["q"], level=it.get("lvl", 1), quantity=inst["n"],
                                price=price, start_bid=start, bid=0, extra={k: v for k, v in inst.items() if k not in ("i", "n")},
                                deposit=deposit, expires_at=time.time() + hours * 3600))
            s.commit()
        p.save_dirty = True
        self.save_player_now(p)
        self.sys(p, f"Angebot erstellt: {it['name']} ×{inst['n']} für {self.fmt_money(price)} (Gebühr {self.fmt_money(deposit)}).")
        self.quest_event(p, "market_post", 1)
        self.send_inventory(p)
        self.send_stats(p)
        self.market_mine(p)

    def market_cancel(self, p: Player, lid: int):
        with SessionLocal() as s:
            r = s.get(MarketListing, int(lid))
            if not r or r.seller_id != p.char_id or r.status != "active":
                return
            if r.bidder_id:
                self.err(p, "Auf dieses Angebot wurde bereits geboten.")
                return
            res = s.execute(update(MarketListing).where(MarketListing.id == r.id, MarketListing.status == "active")
                            .values(status="cancelled"))
            if res.rowcount != 1:
                return
            s.add(Mail(to_id=p.char_id, from_name="Marktplatz", subject="Angebot zurückgezogen",
                       body=f"{r.item_name} ×{r.quantity}", items=[[r.item_id, r.quantity, r.extra or {}]], copper=0))
            s.commit()
        self.sys(p, "Angebot zurückgezogen. Der Gegenstand liegt im Briefkasten.")
        self.mail_notify(p.char_id)
        self.market_mine(p)

    # ================================================================== Kaufen & Bieten
    def market_buy(self, p: Player, lid: int):
        if not self.near_market(p) or not self._rate_ok(p):
            return
        with SessionLocal() as s:
            r = s.get(MarketListing, int(lid))
            if not r or r.status != "active" or r.expires_at < time.time():
                self.err(p, "Dieses Angebot gibt es nicht mehr.")
                return
            if r.seller_id == p.char_id:
                self.err(p, "Ihr könnt Eure eigenen Angebote nicht kaufen.")
                return
            if p.copper < r.price:
                self.err(p, "Nicht genug Geld.")
                return
            res = s.execute(update(MarketListing).where(MarketListing.id == r.id, MarketListing.status == "active")
                            .values(status="sold"))
            if res.rowcount != 1:
                s.rollback()
                self.err(p, "Jemand war schneller.")
                return
            p.copper -= r.price
            fee = int(r.price * SALE_FEE)
            if r.bidder_id:
                s.add(Mail(to_id=r.bidder_id, from_name="Marktplatz", subject="Überboten (Sofortkauf)",
                           body=f"{r.item_name}: Euer Gebot wurde zurückerstattet.", copper=r.bid))
            s.add(Mail(to_id=r.seller_id, from_name="Marktplatz", subject=f"Verkauft: {r.item_name}",
                       body=f"{r.item_name} ×{r.quantity} wurde für {self.fmt_money(r.price)} verkauft. Gebühr: {self.fmt_money(fee)}.",
                       copper=r.price - fee + r.deposit))
            flagged = r.price > 50 * max(1, ITEMS.get(r.item_id, {}).get("sell", 1)) * r.quantity * 20
            s.add(Transaction(buyer_id=p.char_id, seller_id=r.seller_id, kind="market", item_id=r.item_id, quantity=r.quantity,
                              price=r.price, fee=fee, flagged=flagged))
            if flagged:
                log.warning("Auffälliger Marktkauf: %s kauft %s ×%d für %d", p.name, r.item_id, r.quantity, r.price)
            item = (r.item_id, r.quantity, r.extra or {})
            seller_id = r.seller_id
            delivered = p.add_items([(item[0], item[1], False, {k: v for k, v in item[2].items() if k != "b"} or None)])
            if not delivered:
                s.add(Mail(to_id=p.char_id, from_name="Marktplatz", subject=f"Gekauft: {r.item_name}", items=[list(item)]))
            s.commit()
        p.save_dirty = True
        self.save_player_now(p)
        self.sys(p, f"Gekauft: {ITEMS[item[0]]['name']} ×{item[1]}" + ("" if delivered else " (im Briefkasten)"))
        self.mail_notify(seller_id)
        seller = self.by_char.get(seller_id)
        if seller:
            self.progress_counter(seller, "market_sales", 1)
            self.sys(seller, f"Euer Angebot {ITEMS[item[0]]['name']} wurde verkauft!")
        self.send_inventory(p)
        self.send_stats(p)

    def market_bid(self, p: Player, lid: int, amount: int):
        if not self.near_market(p) or not self._rate_ok(p):
            return
        amount = int(amount)
        with SessionLocal() as s:
            r = s.get(MarketListing, int(lid))
            if not r or r.status != "active" or not r.start_bid or r.seller_id == p.char_id:
                return
            min_bid = max(r.start_bid, int(r.bid * 1.05) + 1 if r.bid else r.start_bid)
            if amount < min_bid:
                self.err(p, f"Mindestgebot: {self.fmt_money(min_bid)}")
                return
            if amount >= r.price:
                s.close()
                self.market_buy(p, lid)
                return
            if p.copper < amount:
                self.err(p, "Nicht genug Geld.")
                return
            res = s.execute(update(MarketListing).where(MarketListing.id == r.id, MarketListing.status == "active",
                                                        MarketListing.bid == r.bid).values(bid=amount, bidder_id=p.char_id))
            if res.rowcount != 1:
                s.rollback()
                self.err(p, "Das Gebot wurde inzwischen erhöht.")
                return
            if r.bidder_id:
                s.add(Mail(to_id=r.bidder_id, from_name="Marktplatz", subject=f"Überboten: {r.item_name}",
                           body="Euer Gebot wurde zurückerstattet.", copper=r.bid))
                prev = r.bidder_id
            else:
                prev = None
            p.copper -= amount
            s.commit()
        p.save_dirty = True
        self.save_player_now(p)
        if prev:
            self.mail_notify(prev)
        self.sys(p, f"Gebot abgegeben: {self.fmt_money(amount)}")
        self.send_stats(p)

    def market_expire(self):
        """Abgelaufene Angebote abwickeln (Auktion an Höchstbietenden, sonst zurück an den Verkäufer)."""
        t = time.time()
        notify = set()
        with SessionLocal() as s:
            rows = s.execute(select(MarketListing).where(MarketListing.status == "active", MarketListing.expires_at <= t)
                             .limit(200)).scalars().all()
            for r in rows:
                res = s.execute(update(MarketListing).where(MarketListing.id == r.id, MarketListing.status == "active")
                                .values(status="sold" if r.bidder_id else "expired"))
                if res.rowcount != 1:
                    continue
                if r.bidder_id:
                    fee = int(r.bid * SALE_FEE)
                    s.add(Mail(to_id=r.bidder_id, from_name="Marktplatz", subject=f"Auktion gewonnen: {r.item_name}",
                               items=[[r.item_id, r.quantity, r.extra or {}]]))
                    s.add(Mail(to_id=r.seller_id, from_name="Marktplatz", subject=f"Versteigert: {r.item_name}",
                               body=f"Höchstgebot: {self.fmt_money(r.bid)}. Gebühr: {self.fmt_money(fee)}.",
                               copper=r.bid - fee + r.deposit))
                    s.add(Transaction(buyer_id=r.bidder_id, seller_id=r.seller_id, kind="market", item_id=r.item_id,
                                      quantity=r.quantity, price=r.bid, fee=fee))
                    notify.update({r.bidder_id, r.seller_id})
                else:
                    s.add(Mail(to_id=r.seller_id, from_name="Marktplatz", subject=f"Abgelaufen: {r.item_name}",
                               items=[[r.item_id, r.quantity, r.extra or {}]]))
                    notify.add(r.seller_id)
            s.commit()
        for cid in notify:
            self.mail_notify(cid)

    # ================================================================== Post
    def mail_system(self, char_id: int, subject: str, body: str, items: list, copper: int, currency: dict | None = None):
        with SessionLocal() as s:
            extra_items = [[i, n, {}] for i, n in items]
            m = Mail(to_id=char_id, from_name="Eldornia", subject=subject[:64], body=body, items=extra_items, copper=copper)
            if currency:
                m.body = body + "\n\n" + ", ".join(f"{v}× {k}" for k, v in currency.items())
                m.items = extra_items + [["cur:" + k, v, {}] for k, v in currency.items()]
            s.add(m)
            s.commit()
        self.mail_notify(char_id)

    def mail_notify(self, char_id: int):
        p = self.by_char.get(char_id)
        if p:
            with SessionLocal() as s:
                n = s.execute(select(func.count()).where(Mail.to_id == char_id, Mail.taken == False)).scalar()  # noqa: E712
            self.send(p, {"t": "mail_notify", "unread": n})

    def near_mailbox(self, p: Player) -> bool:
        for e in p.zone.entities.values():
            if p.dist(e) < 7 and ((isinstance(e, GameObj) and e.obj_kind == "mailbox")
                                  or (isinstance(e, Npc) and "mail" in e.tpl.get("services", []))):
                return True
        return False

    def mail_open(self, p: Player):
        if not self.near_mailbox(p):
            self.err(p, "Ihr seid an keinem Briefkasten.")
            return
        with SessionLocal() as s:
            rows = s.execute(select(Mail).where(Mail.to_id == p.char_id, Mail.taken == False)  # noqa: E712
                             .order_by(Mail.id.desc()).limit(50)).scalars().all()
            out = [{"id": r.id, "from": r.from_name, "subject": r.subject, "body": r.body, "items": r.items, "copper": r.copper,
                    "t": r.created_at.timestamp() if r.created_at else 0} for r in rows]
        ids = [i[0] for r in out for i in r["items"] if not str(i[0]).startswith("cur:")]
        self.send(p, {"t": "mail", "list": out, "items": self.item_info_for(p, ids)})

    def mail_take(self, p: Player, mid: int):
        if not self.near_mailbox(p):
            return
        with SessionLocal() as s:
            r = s.get(Mail, int(mid))
            if not r or r.to_id != p.char_id or r.taken:
                return
            items = [i for i in r.items if not str(i[0]).startswith("cur:")]
            curs = [i for i in r.items if str(i[0]).startswith("cur:")]
            if items and not p.can_add([(i[0], i[1], False, {k: v for k, v in (i[2] or {}).items() if k != "b"} or None) for i in items]):
                self.err(p, "Eure Taschen sind voll.")
                return
            res = s.execute(update(Mail).where(Mail.id == r.id, Mail.taken == False).values(taken=True, read=True))  # noqa: E712
            if res.rowcount != 1:
                return
            s.commit()
            copper = r.copper
        p.add_items([(i[0], i[1], bool((i[2] or {}).get("b")), {k: v for k, v in (i[2] or {}).items() if k != "b"} or None) for i in items])
        for c in curs:
            p.add_currency(c[0][4:], int(c[1]))
        p.copper += copper
        p.save_dirty = True
        self.save_player_now(p)
        for i in items:
            self.loot_message(p, i[0], i[1])
        if copper:
            self.sys(p, f"Erhalten: {self.fmt_money(copper)}")
        self.send_inventory(p)
        self.send_stats(p)
        self.mail_open(p)

    def mail_send(self, p: Player, m: dict):
        if not self.near_mailbox(p) or not self._rate_ok(p):
            return
        to = str(m.get("to", "")).strip()
        subject = str(m.get("subject", ""))[:64] or "(kein Betreff)"
        body = str(m.get("body", ""))[:500]
        slots = [s for s in (m.get("slots") or [])[:MAIL_MAX_ITEMS] if isinstance(s, int)]
        copper = max(0, int(m.get("copper", 0) or 0))
        cost = MAIL_COST * max(1, len(slots))
        if p.copper < copper + cost:
            self.err(p, "Nicht genug Geld.")
            return
        insts = []
        for s in set(slots):
            if not (0 <= s < len(p.bags)) or not p.bags[s]:
                return
            inst = p.bags[s]
            if inst.get("b") or ITEMS[inst["i"]].get("quest"):
                self.err(p, "Gebundene Gegenstände können nicht verschickt werden.")
                return
            insts.append((s, inst))
        with SessionLocal() as sess:
            c = sess.execute(select(Character).where(Character.name.ilike(to))).scalar_one_or_none()
            if not c:
                self.err(p, "Empfänger nicht gefunden.")
                return
            if c.id == p.char_id:
                self.err(p, "Ihr könnt Euch nicht selbst schreiben.")
                return
            for s, _ in insts:
                p.bags[s] = None
            p.copper -= copper + cost
            sess.add(Mail(to_id=c.id, from_name=p.name, subject=subject, body=body,
                          items=[[i["i"], i["n"], {k: v for k, v in i.items() if k not in ("i", "n")}] for _, i in insts], copper=copper))
            for _, i in insts:
                sess.add(Transaction(seller_id=p.char_id, buyer_id=c.id, kind="mail", item_id=i["i"], quantity=i["n"]))
            if copper:
                sess.add(Transaction(seller_id=p.char_id, buyer_id=c.id, kind="mail", price=copper, flagged=copper > 10_000_000))
            sess.commit()
            to_id = c.id
            to_name = c.name
        p.save_dirty = True
        self.save_player_now(p)
        self.sys(p, f"Brief an {to_name} verschickt.")
        self.mail_notify(to_id)
        self.send_inventory(p)
        self.send_stats(p)
