"""ASA and Junos mapping gaps, each grounded in vendor syntax we can cite.

Every configuration below uses statements printed in the CIS benchmark audit
text or in the reference configs. Each test checks both directions -- the
setting present decides the control, and the weaker state is not a pass.
"""
from pathlib import Path

from meridian.pipeline import assess

ASA_BASE = """hostname fw1
interface GigabitEthernet1/1
 nameif inside
 security-level 100
ssh 10.0.0.0 255.255.255.0 inside
icmp unreachable rate-limit 1 burst-size 1
"""
ASA_HARDENED = ASA_BASE + """password-policy minimum-length 15
password-policy minimum-uppercase 1
aaa local authentication attempts max-fail 3
password encryption aes
clock timezone UTC 0
logging host inside 10.0.0.9
access-list inside_acl extended deny ip any any
access-group inside_acl in interface inside
"""


def _states(path, text, name):
    p = path / name
    p.write_text(text)
    da = assess(str(p), redact=False, assessment_id="T-GAP")
    return da, {f.control_id: f.state.value for f in da.assessment.findings}


def test_asa_hardened_settings_pass(tmp_path: Path):
    da, s = _states(tmp_path, ASA_HARDENED, "asa.cfg")
    assert da.identity.platform == "cisco_asa"
    for cid in ("MERIDIAN-PWD-001", "MERIDIAN-PWD-002", "MERIDIAN-EXT-013", "MERIDIAN-PLT-002",
                "MERIDIAN-EXT-028", "MERIDIAN-EXT-022", "MERIDIAN-CAT-006", "MERIDIAN-CAT-007",
                "MERIDIAN-CAT-005", "MERIDIAN-EXT-032"):
        assert s[cid] == "PASS", (cid, s[cid])


def test_asa_insecure_defaults_fail_rather_than_vanish(tmp_path: Path):
    _da, s = _states(tmp_path, ASA_BASE, "asa.cfg")
    for cid in ("MERIDIAN-PWD-002", "MERIDIAN-EXT-013", "MERIDIAN-PLT-002", "MERIDIAN-EXT-022",
                "MERIDIAN-CAT-006", "MERIDIAN-CAT-007"):
        assert s[cid] == "FAIL", (cid, s[cid])
    # no password-policy line: the minimum length is unknowable, not zero
    assert s["MERIDIAN-PWD-001"] == "UNKNOWN"


def test_asa_ssh_version_is_unknown_not_excused(tmp_path: Path):
    _da, s = _states(tmp_path, ASA_BASE, "asa.cfg")
    assert s["MERIDIAN-SSH-002"] == "UNKNOWN", "the old 'no selector exists' exclusion was wrong"


JUNOS = """version 21.4R3.15;
system {{
    host-name r1;
    time-zone UTC;
    root-authentication {{
        encrypted-password "$6$hash";
    }}
    login {{
        retry-options {{
            tries-before-disconnect 3;
            lockout-period 30;
        }}
    }}
    ports {{
        auxiliary disable;
    }}
    services {{
        ssh {{
            protocol-version v2;
{ssh}
        }}
    }}
    syslog {{
        host 10.0.0.9 {{
            any notice;
        }}
        file cmdlog {{
            interactive-commands any;
        }}
    }}
}}
"""


def test_junos_grounded_settings_decide_controls(tmp_path: Path):
    _da, s = _states(tmp_path, JUNOS.format(ssh=""), "srx.conf")
    for cid in ("MERIDIAN-EXT-013", "MERIDIAN-EXT-009", "MERIDIAN-EXT-017", "MERIDIAN-EXT-028",
                "MERIDIAN-EXT-041", "MERIDIAN-PWD-003", "MERIDIAN-EXT-022", "MERIDIAN-EXT-018"):
        assert s[cid] == "PASS", (cid, s[cid])
    assert s["MERIDIAN-EXT-012"] == "NOT_APPLICABLE", "Junos has no enable secret"


def test_junos_weak_crypto_is_judged_by_the_cis_rule(tmp_path: Path):
    # no cipher statement: the default set is release-dependent -> undecided
    _da, s = _states(tmp_path, JUNOS.format(ssh=""), "a.conf")
    assert s["MERIDIAN-SSH-003"] == "UNKNOWN"
    # strong only -> pass (previously any configured cipher failed)
    _da, s = _states(tmp_path, JUNOS.format(
        ssh="            ciphers [ aes256-ctr aes128-ctr ];\n"
            "            key-exchange [ ecdh-sha2-nistp256 curve25519-sha256 ];"), "b.conf")
    assert s["MERIDIAN-SSH-003"] == "PASS" and s["MERIDIAN-EXT-001"] == "PASS"
    # a weak cipher or key exchange -> fail
    _da, s = _states(tmp_path, JUNOS.format(
        ssh="            ciphers [ aes256-ctr arcfour ];\n"
            "            key-exchange [ dh-group1-sha1 ];"), "c.conf")
    assert s["MERIDIAN-SSH-003"] == "FAIL" and s["MERIDIAN-EXT-001"] == "FAIL"


IOS = """hostname r1
version 17.9
ip ssh version 2
{algo}line vty 0 4
 transport input ssh
"""


def test_ios_weak_crypto_is_not_passed_on_an_assumption(tmp_path: Path):
    """No `ip ssh server algorithm` line: the IOS default depends on the
    release, so "no weak ciphers" cannot be claimed. It used to PASS."""
    _da, s = _states(tmp_path, IOS.format(algo=""), "a.cfg")
    assert s["MERIDIAN-SSH-003"] == "UNKNOWN"

    _da, s = _states(tmp_path, IOS.format(
        algo="ip ssh server algorithm encryption aes256-ctr aes128-ctr\n"), "b.cfg")
    assert s["MERIDIAN-SSH-003"] == "PASS", "stated and strong"

    _da, s = _states(tmp_path, IOS.format(
        algo="ip ssh server algorithm encryption aes256-ctr 3des-cbc\n"), "c.cfg")
    assert s["MERIDIAN-SSH-003"] == "FAIL"


def test_urpf_is_not_ip_source_guard(tmp_path: Path):
    da, _s = _states(tmp_path, IOS.format(algo="") +
                     "interface Gi0/1\n ip verify unicast source reachable-via rx\n", "d.cfg")
    obs = da.sbm.get("l2.ip_source_guard")
    assert obs is None or obs.value is not True, "uRPF satisfied the IP Source Guard control"


def test_a_junos_community_means_v2c_is_in_use(tmp_path: Path):
    text = JUNOS.format(ssh="") + "snmp {\n    community ops {\n        authorization read-only;\n    }\n}\n"
    _da, s = _states(tmp_path, text, "d.conf")
    assert s["MERIDIAN-SNMP-001"] == "FAIL"
