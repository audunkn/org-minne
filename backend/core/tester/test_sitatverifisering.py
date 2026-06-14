"""
Enhetstester for llm/sitatverifisering.py.
"""
import sys
import os

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))


# ---------------------------------------------------------------------------
# parse_sitater
# ---------------------------------------------------------------------------

class TestParseSitater:

    def test_ingen_sitater_sekson(self):
        """Ingen Sitater-seksjon → tom liste."""
        from llm.sitatverifisering import parse_sitater
        tekst = "Analyse: Omsetningen økte markant i Q3."
        assert parse_sitater(tekst) == []

    def test_tom_sitater_seksjon(self):
        """Sitater-seksjon finnes men er tom → tom liste."""
        from llm.sitatverifisering import parse_sitater
        tekst = "Analyse: Omsetningen økte.\n\nSitater:"
        assert parse_sitater(tekst) == []

    def test_ett_sitat(self):
        """Én bullet returneres som étt element i listen."""
        from llm.sitatverifisering import parse_sitater
        tekst = "Analyse: Noe.\n\nSitater:\n• Vi økte omsetningen med 12 prosent."
        assert parse_sitater(tekst) == ["Vi økte omsetningen med 12 prosent."]

    def test_tre_sitater(self):
        """Tre bullets returneres som tre elementer."""
        from llm.sitatverifisering import parse_sitater
        tekst = (
            "Analyse: Noe.\n\nSitater:\n"
            "• Sitat én.\n"
            "• Sitat to.\n"
            "• Sitat tre."
        )
        assert parse_sitater(tekst) == ["Sitat én.", "Sitat to.", "Sitat tre."]

    def test_whitespace_strippes(self):
        """Ledende/etterfølgende whitespace strippes fra hvert sitat."""
        from llm.sitatverifisering import parse_sitater
        tekst = "Analyse: X.\n\nSitater:\n•   Sitat med mellomrom.   "
        assert parse_sitater(tekst) == ["Sitat med mellomrom."]


# ---------------------------------------------------------------------------
# verifiser_sitat
# ---------------------------------------------------------------------------

class TestVerifiserSitat:

    def test_identisk_match(self):
        """Eksakt substring-match returnerer True."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Selskapet økte omsetningen med 12 prosent i fjerde kvartal."
        sitat = "Selskapet økte omsetningen med 12 prosent i fjerde kvartal."
        assert verifiser_sitat(sitat, transkripsjon) is True

    def test_normalisert_whitespace_match(self):
        """Sitat med én linje matcher transkripsjon med linjeskift midt i setningen."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Selskapet økte omsetningen\nmed 12 prosent i fjerde kvartal."
        sitat = "Selskapet økte omsetningen med 12 prosent i fjerde kvartal."
        assert verifiser_sitat(sitat, transkripsjon) is True

    def test_ingen_match_hallusinert_sitat(self):
        """Hallusinert sitat som ikke finnes i transkripsjonen → False."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Omsetningen økte med 5 prosent."
        sitat = "Kostnadene falt dramatisk i tredje kvartal pga effektiviseringsprogrammet."
        assert verifiser_sitat(sitat, transkripsjon) is False

    def test_for_kort_sitat_returnerer_false(self):
        """Sitat kortere enn 10 tegn → False (unngå falske treff)."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Ja, vi leverte gode resultater."
        sitat = "Ja"
        assert verifiser_sitat(sitat, transkripsjon) is False

    def test_prefiks_strippes_før_match(self):
        """[Bedrift]-prefiks fjernes før matching."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Vi leverte sterke resultater i alle segmenter dette kvartalet."
        sitat = "[EDP] Vi leverte sterke resultater i alle segmenter dette kvartalet."
        assert verifiser_sitat(sitat, transkripsjon) is True

    def test_nøyaktig_ti_tegn_er_ok(self):
        """Sitat med eksakt 10 tegn etter normalisering er tillatt."""
        from llm.sitatverifisering import verifiser_sitat
        # 10 tegn: "1234567890"
        transkripsjon = "abcde 1234567890 fghij"
        sitat = "1234567890"
        assert verifiser_sitat(sitat, transkripsjon) is True

    def test_ni_tegn_returnerer_false(self):
        """Sitat med 9 tegn etter normalisering → False."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "abcde 123456789 fghij"
        sitat = "123456789"
        assert verifiser_sitat(sitat, transkripsjon) is False

    def test_markdown_wrapper_strippes(self):
        """LLM wrapper *\"tekst\"* — asterisk og anførselstegn strippes før match."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Nettoresultatet for konsernet var opp til 4 723 millioner kroner."
        sitat = '*"Nettoresultatet for konsernet var opp til 4 723 millioner kroner."*'
        assert verifiser_sitat(sitat, transkripsjon) is True

    def test_typografiske_anforselstegn_strippes(self):
        """Typografiske \u201c\u201d-anf\xf8rselstegn strippes f\xf8r match."""
        from llm.sitatverifisering import verifiser_sitat
        transkripsjon = "Inntektene \xf8kte med 42 prosent p\xe5 \xe5rsbasis dette kvartalet."
        sitat = "\u201cInntektene \xf8kte med 42 prosent p\xe5 \xe5rsbasis dette kvartalet.\u201d"
        assert verifiser_sitat(sitat, transkripsjon) is True


# ---------------------------------------------------------------------------
# filtrer_sitater
# ---------------------------------------------------------------------------

class TestFiltrerSitater:

    _TRANSKRIPSJON = (
        "Selskapet økte omsetningen med 12 prosent i fjerde kvartal. "
        "Kostnadene ble redusert som følge av restruktureringsprogrammet. "
        "Dette er et ekte sitat fra transkripsjon."
    )

    def test_blanding_beholder_kun_reelle(self):
        """Blanding av reelle og hallusinerte sitater — kun reelle beholdes."""
        from llm.sitatverifisering import filtrer_sitater
        tekst = (
            "Analyse: Omsetningen økte markant.\n\nSitater:\n"
            "• Selskapet økte omsetningen med 12 prosent i fjerde kvartal.\n"
            "• Hallusinert setning som ikke finnes noe sted i transkripsjonen."
        )
        resultat = filtrer_sitater(tekst, self._TRANSKRIPSJON)
        assert "Selskapet økte omsetningen med 12 prosent i fjerde kvartal." in resultat
        assert "Hallusinert setning" not in resultat
        assert "Sitater:" in resultat

    def test_alle_hallusinerte_gir_tom_sitater_seksjon(self):
        """Alle sitater hallusinerte → Sitater:-linje beholdes, ingen bullets."""
        from llm.sitatverifisering import filtrer_sitater
        tekst = (
            "Analyse: Noe skjedde.\n\nSitater:\n"
            "• Hallusinert sitat nummer én som ikke finnes.\n"
            "• Enda et hallusinert sitat som heller ikke finnes."
        )
        resultat = filtrer_sitater(tekst, self._TRANSKRIPSJON)
        assert "Sitater:" in resultat
        assert "•" not in resultat

    def test_analysen_bevares_uendret(self):
        """Analyse-seksjonen forblir uendret etter filtrering."""
        from llm.sitatverifisering import filtrer_sitater
        analyse_tekst = "Analyse: Omsetningen økte markant pga høye energipriser."
        tekst = (
            f"{analyse_tekst}\n\nSitater:\n"
            "• Hallusinert sitat som ikke finnes."
        )
        resultat = filtrer_sitater(tekst, self._TRANSKRIPSJON)
        assert analyse_tekst in resultat

    def test_alle_reelle_beholdes(self):
        """Alle sitater reelle → alle beholdes i output."""
        from llm.sitatverifisering import filtrer_sitater
        tekst = (
            "Analyse: Dobbel forbedring.\n\nSitater:\n"
            "• Selskapet økte omsetningen med 12 prosent i fjerde kvartal.\n"
            "• Dette er et ekte sitat fra transkripsjon."
        )
        resultat = filtrer_sitater(tekst, self._TRANSKRIPSJON)
        assert "Selskapet økte omsetningen med 12 prosent i fjerde kvartal." in resultat
        assert "Dette er et ekte sitat fra transkripsjon." in resultat

    def test_ingen_sitater_seksjon_returnerer_tekst_uendret(self):
        """Tekst uten Sitater-seksjon returneres uendret."""
        from llm.sitatverifisering import filtrer_sitater
        tekst = "Analyse: Ingen sitater i denne svaret."
        resultat = filtrer_sitater(tekst, self._TRANSKRIPSJON)
        assert resultat == tekst
