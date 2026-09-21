"""Unit tests for the scanner firewall module."""

import subprocess
from unittest import mock

from ostorlab.scanner import firewall


@mock.patch("ostorlab.scanner.firewall.flush_blacklist")
@mock.patch("subprocess.run")
def testEnsureFirewallChains_always_includesWaitFlagAndDoesNotFlush(
    mock_run: mock.MagicMock,
    mock_flush: mock.MagicMock,
) -> None:
    """Ensure chains include -w 10 flag and flush_blacklist is never called."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.ensure_firewall_chains()

    assert result is True
    mock_flush.assert_not_called()
    assert mock_run.call_count == 4
    for call in mock_run.call_args_list:
        cmd = call[0][0]
        assert cmd[1] == "-w"
        assert cmd[2] == "10"


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
            ["iptables", "-w", "10", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-C",
                "DOCKER-USER",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
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
            ["ip6tables", "-w", "10", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-C",
                "DOCKER-USER",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
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
            ["iptables", "-w", "10", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-C",
                "DOCKER-USER",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-w", "10", "-N", "OXO_EGRESS_FILTER"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-C",
                "DOCKER-USER",
                "-j",
                "OXO_EGRESS_FILTER",
            ],
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
        ["iptables", "-w", "10", "-N", "OXO_EGRESS_FILTER"],
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
def testApplyScanBlacklist_whenValidIps_createsChainPopulatesRulesAndInsertsJump(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure per-scan chain is created, populated with DROP rules, and jumped to."""

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

    result = firewall.apply_scan_blacklist(
        scan_id=42, ips=["1.2.3.4", "10.0.0.0/8", "2001:db8::1"]
    )

    assert result is True
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-w", "10", "-N", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-w", "10", "-F", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-A",
                "OXO_SCAN_42",
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
                "-w",
                "10",
                "-A",
                "OXO_SCAN_42",
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
                "iptables",
                "-w",
                "10",
                "-C",
                "OXO_EGRESS_FILTER",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-I",
                "OXO_EGRESS_FILTER",
                "1",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-w", "10", "-N", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-w", "10", "-F", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-A",
                "OXO_SCAN_42",
                "-d",
                "2001:db8::1",
                "-j",
                "DROP",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-C",
                "OXO_EGRESS_FILTER",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-I",
                "OXO_EGRESS_FILTER",
                "1",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testApplyScanBlacklist_whenEmptyIps_returnsTrueWithoutExecutingCommands(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_scan_blacklist returns True without executing commands
    when ips is empty.
    """
    result = firewall.apply_scan_blacklist(scan_id=42, ips=[])

    assert result is True
    mock_run.assert_not_called()


@mock.patch("subprocess.run")
def testApplyScanBlacklist_whenInvalidIps_skipsInvalidAndReturnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure invalid IPs are skipped, valid ones applied, and False is returned."""

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

    result = firewall.apply_scan_blacklist(
        scan_id=42, ips=["1.2.3.4", "invalid-domain.com", "1.2.3.4; rm -rf /"]
    )

    assert result is False
    assert mock_run.call_args_list == [
        mock.call(
            ["iptables", "-w", "10", "-N", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-w", "10", "-F", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-A",
                "OXO_SCAN_42",
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
                "-w",
                "10",
                "-C",
                "OXO_EGRESS_FILTER",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-I",
                "OXO_EGRESS_FILTER",
                "1",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testClearScanBlacklist_whenCalled_removesJumpFlushesAndDeletesChain(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure clear_scan_blacklist removes jump, flushes and deletes per-scan chain."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.clear_scan_blacklist(scan_id=42)

    assert result is True
    assert mock_run.call_args_list == [
        mock.call(
            [
                "iptables",
                "-w",
                "10",
                "-D",
                "OXO_EGRESS_FILTER",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-w", "10", "-F", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["iptables", "-w", "10", "-X", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            [
                "ip6tables",
                "-w",
                "10",
                "-D",
                "OXO_EGRESS_FILTER",
                "-j",
                "OXO_SCAN_42",
            ],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-w", "10", "-F", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
        mock.call(
            ["ip6tables", "-w", "10", "-X", "OXO_SCAN_42"],
            capture_output=True,
            check=False,
        ),
    ]


@mock.patch("subprocess.run")
def testClearScanBlacklist_whenChainDoesNotExist_handlesGracefullyAndReturnsTrue(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure clear_scan_blacklist handles missing chains and rules gracefully."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-D" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                returncode=1,
                stdout=b"",
                stderr=b"iptables: Bad rule (does a matching rule exist?)",
            )
        if "-F" in cmd or "-X" in cmd:
            return subprocess.CompletedProcess(
                cmd,
                returncode=1,
                stdout=b"",
                stderr=b"iptables: No chain/target/match by that name.",
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.clear_scan_blacklist(scan_id=42)

    assert result is True


@mock.patch("ostorlab.scanner.firewall.clear_scan_blacklist")
@mock.patch("subprocess.run")
def testCleanupOrphanedChains_whenOrphanedChainsPresent_clearsOnlyOrphaned(
    mock_run: mock.MagicMock,
    mock_clear: mock.MagicMock,
) -> None:
    """Ensure cleanup_orphaned_chains parses -S output and clears only dead
    scan chains.
    """

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if cmd[0] == "iptables":
            stdout = (
                b"-P INPUT ACCEPT\n"
                b"-N OXO_EGRESS_FILTER\n"
                b"-N OXO_SCAN_10\n"
                b"-N OXO_SCAN_20\n"
            )
        else:
            stdout = (
                b"-P INPUT ACCEPT\n"
                b"-N OXO_EGRESS_FILTER\n"
                b"-N OXO_SCAN_20\n"
                b"-N OXO_SCAN_30\n"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=stdout, stderr=b"")

    mock_run.side_effect = run_side_effect

    firewall.cleanup_orphaned_chains(active_scan_ids={20})

    assert mock_clear.call_count == 2
    mock_clear.assert_has_calls([mock.call(10), mock.call(30)], any_order=True)


@mock.patch("subprocess.run")
def testApplyScanBlacklist_whenIpContainsNonStringOrNone_returnsFalseWithoutCrashing(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure non-string and None IP inputs are handled safely and return False."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_scan_blacklist(
        scan_id=42,
        ips=["1.1.1.1", None, 12345],  # type: ignore[list-item]
    )

    assert result is False


@mock.patch("subprocess.run")
def testApplyScanBlacklist_whenDropAppendFails_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure apply_scan_blacklist returns False when DROP rule append fails."""

    def run_side_effect(
        cmd: list[str],
        capture_output: bool = True,
        check: bool = False,
    ) -> subprocess.CompletedProcess[bytes]:
        del capture_output, check
        if "-A" in cmd:
            return subprocess.CompletedProcess(
                cmd, returncode=1, stdout=b"", stderr=b"permission denied"
            )
        return subprocess.CompletedProcess(cmd, returncode=0, stdout=b"", stderr=b"")

    mock_run.side_effect = run_side_effect

    result = firewall.apply_scan_blacklist(scan_id=42, ips=["1.1.1.1"])

    assert result is False


@mock.patch("subprocess.run")
def testApplyScanBlacklist_whenDuplicateIpsProvided_deduplicatesRules(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure duplicate IPs are deduplicated before adding DROP rules."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_scan_blacklist(
        scan_id=42, ips=["1.1.1.1", "1.1.1.1", "2.2.2.2"]
    )

    assert result is True
    append_calls = [call for call in mock_run.call_args_list if "-A" in call[0][0]]
    assert len(append_calls) == 2


@mock.patch("subprocess.run")
def testClearScanBlacklist_whenCommandFails_returnsFalse(
    mock_run: mock.MagicMock,
) -> None:
    """Ensure clear_scan_blacklist returns False when command execution fails."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=1, stdout=b"", stderr=b"permission denied"
    )

    result = firewall.clear_scan_blacklist(scan_id=42)

    assert result is False


@mock.patch("subprocess.run")
def testApplyBlacklist_whenValidIps_returnsTrue(
    mock_run: mock.MagicMock,
) -> None:
    """Smoke test for legacy apply_blacklist with wait flag."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.apply_blacklist(["1.1.1.1"])

    assert result is True


@mock.patch("subprocess.run")
def testFlushBlacklist_whenCalled_returnsTrue(
    mock_run: mock.MagicMock,
) -> None:
    """Smoke test for legacy flush_blacklist with wait flag."""
    mock_run.return_value = subprocess.CompletedProcess(
        [], returncode=0, stdout=b"", stderr=b""
    )

    result = firewall.flush_blacklist()

    assert result is True
