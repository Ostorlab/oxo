"""Unit tests for the scanner firewall module."""

import subprocess
from unittest import mock

from ostorlab.scanner import firewall


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenChainsDoNotExist_createsChainsAndInsertsJump(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure chains are created and jump rules are inserted when not present."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-C" in cmd:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout=b"", stderr=b"rule not found"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.ensure_firewall_chains()

    assert result is True
    assert mock_run.call_count == 6
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-C", "DOCKER-USER", "-j", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-I",
                "DOCKER-USER",
                "1",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-C", "DOCKER-USER", "-j", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-I",
                "DOCKER-USER",
                "1",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenChainsAlreadyExist_doesNotInsertJumpAgain(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure jump rules are not inserted if they already exist."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-N" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                returncode=1,
                stdout=b"",
                stderr=b"iptables: Chain already exists.",
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.ensure_firewall_chains()

    assert result is True
    assert mock_run.call_count == 4
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-C", "DOCKER-USER", "-j", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-C", "DOCKER-USER", "-j", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenBinaryNotFound_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is handled gracefully when iptables is missing."""
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'iptables'")

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenPermissionDenied_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is handled gracefully when permission is denied."""
    mock_run.side_effect = PermissionError("Permission denied")

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenChainCreationFails_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is returned when chain creation fails with non-zero exit."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["iptables", "-N", "OXO_EGRESS_FILTER"],
        returncode=2,
        stdout=b"",
        stderr=b"iptables: Memory allocation failed",
    )

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenJumpInsertionFails_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is returned when jump rule insertion fails."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-C" in cmd:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout=b"", stderr=b"rule not found"
            )
        if "-I" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                returncode=1,
                stdout=b"",
                stderr=b"iptables: No chain/target/match by that name",
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenOsError_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is handled gracefully when an OSError occurs."""
    mock_run.side_effect = OSError("Generic OS error")

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenJumpInsertionReturnsNone_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is returned when jump insertion command returns None."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes] | None:
        del capture_output, check
        if "-C" in cmd:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout=b"", stderr=b"rule not found"
            )
        if "-I" in cmd:
            raise OSError("Execution failed")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testEnsureFirewallChains_whenCheckJumpReturnsNone_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure failure is returned when jump check command returns None."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes] | None:
        del capture_output, check
        if "-C" in cmd:
            raise OSError("Execution failed")
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.ensure_firewall_chains()

    assert result is False


@mock.patch("subprocess.run")
def testApplyBlacklist_whenMixedValidAndInvalidIps_appliesValidAndSkipsInvalid(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure valid IPv4 and IPv6 addresses are added and invalid ones skipped."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    ips = [
        "1.2.3.4",
        "10.0.0.0/8",
        "2001:db8::/32",
        "invalid-domain.com",
        "1.2.3.4; rm -rf /",
    ]

    result = firewall.apply_blacklist(ips)

    assert result is False
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-F", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-F", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-A",
                "OXO_EGRESS_FILTER",
                "-d",
                "1.2.3.4",
                "-j",
                "DROP",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-A",
                "OXO_EGRESS_FILTER",
                "-d",
                "10.0.0.0/8",
                "-j",
                "DROP",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-A",
                "OXO_EGRESS_FILTER",
                "-d",
                "2001:db8::/32",
                "-j",
                "DROP",
            ],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testApplyBlacklist_whenAllIpsValidAndCommandSucceeds_returnsTrue(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_blacklist returns True when all rules are applied successfully."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_blacklist(["1.2.3.4", "2001:db8::1"])

    assert result is True


@mock.patch("subprocess.run")
def testApplyBlacklist_whenEmptyIps_returnsTrue(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_blacklist returns True when ips list is empty."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_blacklist([])

    assert result is True


@mock.patch("subprocess.run")
def testApplyBlacklist_whenCommandFails_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_blacklist returns False when command returns non-zero code."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-A" in cmd:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout=b"", stderr=b"iptables error"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.apply_blacklist(["1.2.3.4"])

    assert result is False


@mock.patch("ostorlab.scanner.firewall.flush_blacklist")
@mock.patch("subprocess.run")
def testApplyBlacklist_whenCalled_flushesBlacklistFirst(
    mock_run: mock.MagicMock,
    mock_flush: mock.MagicMock,
) -> None:
    """Ensure apply_blacklist flushes existing rules before adding new ones."""
    mock_flush.return_value = True
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_blacklist(["192.168.1.1"])

    mock_flush.assert_called_once()
    assert result is True


@mock.patch("subprocess.run")
@mock.patch("ostorlab.scanner.firewall.flush_blacklist")
def testApplyBlacklist_whenFlushFails_returnsFalse(
    mock_flush: mock.MagicMock,
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_blacklist returns False when initial flush fails."""
    mock_flush.return_value = False

    result = firewall.apply_blacklist(["192.168.1.1"])

    assert result is False
    mock_run.assert_not_called()


@mock.patch("subprocess.run")
def testFlushBlacklist_whenCalled_flushesIptablesAndIp6tables(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure flush_blacklist executes flush on both iptables and ip6tables."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.flush_blacklist()

    assert result is True
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-F", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-F", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testFlushBlacklist_whenChainNotFound_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure flush_blacklist returns False when command exits non-zero."""
    mock_run.return_value = subprocess.CompletedProcess(
        ["iptables", "-F", "OXO_EGRESS_FILTER"],
        returncode=1,
        stdout=b"",
        stderr=b"iptables: No chain/target/match by that name.",
    )

    result = firewall.flush_blacklist()

    assert result is False


@mock.patch("subprocess.run")
def testFlushBlacklist_whenBinaryNotFound_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure flush_blacklist returns False when binary is missing."""
    mock_run.side_effect = FileNotFoundError("No such file or directory: 'iptables'")

    result = firewall.flush_blacklist()

    assert result is False
