"""Firewall management for scan network isolation using iptables."""

import ipaddress
import logging
import subprocess

logger = logging.getLogger(__name__)

OXO_EGRESS_FILTER_CHAIN = "OXO_EGRESS_FILTER"
DOCKER_USER_CHAIN = "DOCKER-USER"
IPTABLES_BIN = "iptables"
IP6TABLES_BIN = "ip6tables"
IPTABLES_WAIT_TIMEOUT = "10"
OXO_SCAN_PREFIX = "OXO_SCAN_"


def _execute_command(cmd: list[str]) -> subprocess.CompletedProcess[bytes] | None:
    try:
        return subprocess.run(
            cmd,
            capture_output=True,
            check=False,
        )
    except FileNotFoundError:
        logger.warning("Command not found: %s", cmd[0])
        return None
    except PermissionError:
        logger.warning("Permission denied executing: %s", cmd[0])
        return None
    except OSError as error:
        logger.warning("OS error executing command %s: %s", cmd[0], error)
        return None


def _validate_ip(
    ip: object,
) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    if isinstance(ip, str) is False:
        logger.warning("Invalid IP address type: %s", type(ip))
        return None
    try:
        return ipaddress.ip_network(str(ip), strict=False)
    except ValueError:
        logger.warning("Invalid IP address or network: %s", ip)
        return None
    except TypeError:
        logger.warning("Invalid IP address type: %s", type(ip))
        return None


def _scan_chain_name(scan_id: int) -> str:
    return f"{OXO_SCAN_PREFIX}{scan_id}"


def _ensure_chain(binary: str, chain: str) -> bool:
    result = _execute_command([binary, "-w", IPTABLES_WAIT_TIMEOUT, "-N", chain])
    if result is None:
        return False
    if result.returncode == 0:
        return True
    if ("already exists" in result.stderr.decode(errors="ignore").lower()) is True:
        logger.debug("Chain %s already exists in %s", chain, binary)
        return True
    logger.warning(
        "Failed to create chain %s in %s: %s",
        chain,
        binary,
        result.stderr.decode(errors="ignore"),
    )
    return False


def _flush_chain(binary: str, chain: str) -> bool:
    result = _execute_command([binary, "-w", IPTABLES_WAIT_TIMEOUT, "-F", chain])
    if result is None:
        logger.warning("Could not flush chain %s with %s", chain, binary)
        return False
    if result.returncode == 0:
        logger.debug("Successfully flushed chain %s in %s", chain, binary)
        return True
    stderr_lower = result.stderr.decode(errors="ignore").lower()
    if ("no chain" in stderr_lower or "does not exist" in stderr_lower) is True:
        logger.debug("Chain %s does not exist in %s for flush", chain, binary)
        return True
    logger.warning(
        "Chain %s flush returned non-zero with %s: %s",
        chain,
        binary,
        result.stderr.decode(errors="ignore"),
    )
    return False


def _delete_chain(binary: str, chain: str) -> bool:
    result = _execute_command([binary, "-w", IPTABLES_WAIT_TIMEOUT, "-X", chain])
    if result is None:
        logger.warning("Could not delete chain %s with %s", chain, binary)
        return False
    if result.returncode == 0:
        logger.debug("Successfully deleted chain %s in %s", chain, binary)
        return True
    stderr_lower = result.stderr.decode(errors="ignore").lower()
    if ("no chain" in stderr_lower or "does not exist" in stderr_lower) is True:
        logger.debug("Chain %s does not exist in %s for delete", chain, binary)
        return True
    logger.warning(
        "Chain %s delete returned non-zero with %s: %s",
        chain,
        binary,
        result.stderr.decode(errors="ignore"),
    )
    return False


def _ensure_jump_rule(binary: str, parent_chain: str, target_chain: str) -> bool:
    check_result = _execute_command(
        [
            binary,
            "-w",
            IPTABLES_WAIT_TIMEOUT,
            "-C",
            parent_chain,
            "-j",
            target_chain,
        ]
    )
    if check_result is None:
        return False
    if check_result.returncode == 0:
        return True

    insert_result = _execute_command(
        [
            binary,
            "-w",
            IPTABLES_WAIT_TIMEOUT,
            "-I",
            parent_chain,
            "1",
            "-j",
            target_chain,
        ]
    )
    if insert_result is None or insert_result.returncode != 0:
        error_msg = (
            insert_result.stderr.decode(errors="ignore")
            if insert_result is not None
            else "command failed"
        )
        logger.warning(
            "Failed to insert jump rule from %s to %s in %s: %s",
            parent_chain,
            target_chain,
            binary,
            error_msg,
        )
        return False
    return True


def _remove_jump_rule(binary: str, parent_chain: str, target_chain: str) -> bool:
    result = _execute_command(
        [
            binary,
            "-w",
            IPTABLES_WAIT_TIMEOUT,
            "-D",
            parent_chain,
            "-j",
            target_chain,
        ]
    )
    if result is None:
        logger.warning(
            "Could not remove jump rule from %s to %s with %s",
            parent_chain,
            target_chain,
            binary,
        )
        return False
    if result.returncode == 0:
        logger.debug(
            "Successfully removed jump rule from %s to %s in %s",
            parent_chain,
            target_chain,
            binary,
        )
        return True
    stderr_lower = result.stderr.decode(errors="ignore").lower()
    if (
        "does a matching rule exist" in stderr_lower
        or "no chain" in stderr_lower
        or "does not exist" in stderr_lower
        or "bad rule" in stderr_lower
    ) is True:
        logger.debug(
            "Jump rule from %s to %s does not exist in %s",
            parent_chain,
            target_chain,
            binary,
        )
        return True
    logger.warning(
        "Failed to remove jump rule from %s to %s in %s: %s",
        parent_chain,
        target_chain,
        binary,
        result.stderr.decode(errors="ignore"),
    )
    return False


def ensure_firewall_chains() -> bool:
    """Ensure OXO_EGRESS_FILTER chain exists and is hooked into DOCKER-USER."""
    for binary in (IPTABLES_BIN, IP6TABLES_BIN):
        if _ensure_chain(binary, OXO_EGRESS_FILTER_CHAIN) is False:
            return False
        if (
            _ensure_jump_rule(binary, DOCKER_USER_CHAIN, OXO_EGRESS_FILTER_CHAIN)
            is False
        ):
            return False
    return True


def apply_scan_blacklist(scan_id: int, ips: list[str]) -> bool:
    """Create a per-scan chain and populate it with DROP rules for blacklisted IPs."""
    if len(ips) == 0:
        return True

    chain_name = _scan_chain_name(scan_id)
    all_success = True
    ipv4_targets: list[str] = []
    ipv6_targets: list[str] = []

    for ip in ips:
        network = _validate_ip(ip)
        if network is None:
            all_success = False
            continue
        target = (
            str(network.network_address)
            if network.num_addresses == 1 and "/" not in str(ip)
            else str(network)
        )
        if isinstance(network, ipaddress.IPv4Network) is True:
            ipv4_targets.append(target)
        else:
            ipv6_targets.append(target)

    targets_by_binary = [
        (IPTABLES_BIN, ipv4_targets),
        (IP6TABLES_BIN, ipv6_targets),
    ]

    for binary, targets in targets_by_binary:
        if len(targets) == 0:
            continue
        if _ensure_chain(binary, chain_name) is False:
            all_success = False
            continue
        if _flush_chain(binary, chain_name) is False:
            all_success = False
            continue
        for target in targets:
            result = _execute_command(
                [
                    binary,
                    "-w",
                    IPTABLES_WAIT_TIMEOUT,
                    "-A",
                    chain_name,
                    "-d",
                    target,
                    "-j",
                    "DROP",
                ]
            )
            if result is None or result.returncode != 0:
                error_msg = (
                    result.stderr.decode(errors="ignore")
                    if result is not None
                    else "command failed"
                )
                logger.warning(
                    "Failed to append DROP rule for %s in %s: %s",
                    target,
                    chain_name,
                    error_msg,
                )
                all_success = False
        if _ensure_jump_rule(binary, OXO_EGRESS_FILTER_CHAIN, chain_name) is False:
            all_success = False

    return all_success


def clear_scan_blacklist(scan_id: int) -> bool:
    """Remove jump rule, flush and delete the per-scan chain."""
    chain_name = _scan_chain_name(scan_id)
    all_success = True
    for binary in (IPTABLES_BIN, IP6TABLES_BIN):
        if _remove_jump_rule(binary, OXO_EGRESS_FILTER_CHAIN, chain_name) is False:
            all_success = False
        if _flush_chain(binary, chain_name) is False:
            all_success = False
        if _delete_chain(binary, chain_name) is False:
            all_success = False
    return all_success


def cleanup_orphaned_chains(active_scan_ids: set[int]) -> None:
    """Clean up any scan chains that do not belong to active scans."""
    orphaned_scan_ids: set[int] = set()
    for binary in (IPTABLES_BIN, IP6TABLES_BIN):
        result = _execute_command([binary, "-w", IPTABLES_WAIT_TIMEOUT, "-S"])
        if result is None or result.returncode != 0:
            continue
        output = result.stdout.decode(errors="ignore")
        for line in output.splitlines():
            line = line.strip()
            if line.startswith(f"-N {OXO_SCAN_PREFIX}") is True:
                scan_id_part = line[len(f"-N {OXO_SCAN_PREFIX}") :].strip()
                if scan_id_part.isdigit() is True:
                    scan_id = int(scan_id_part)
                    if scan_id not in active_scan_ids:
                        orphaned_scan_ids.add(scan_id)
    for scan_id in sorted(orphaned_scan_ids):
        clear_scan_blacklist(scan_id)


def flush_blacklist() -> bool:
    """Flush all rules in OXO_EGRESS_FILTER chain for IPv4 and IPv6."""
    all_success = True
    for binary in (IPTABLES_BIN, IP6TABLES_BIN):
        if _flush_chain(binary, OXO_EGRESS_FILTER_CHAIN) is False:
            all_success = False
    return all_success


def apply_blacklist(ips: list[str]) -> bool:
    """Flush and apply blacklist DROP rules for the given IPs and networks."""
    flush_success = flush_blacklist()
    if len(ips) == 0 or flush_success is False:
        return flush_success

    all_success: bool = True
    for ip in ips:
        network = _validate_ip(ip)
        if network is None:
            all_success = False
            continue
        target = (
            str(network.network_address)
            if network.num_addresses == 1 and "/" not in str(ip)
            else str(network)
        )
        binary = (
            IPTABLES_BIN
            if isinstance(network, ipaddress.IPv4Network) is True
            else IP6TABLES_BIN
        )
        result = _execute_command(
            [
                binary,
                "-w",
                IPTABLES_WAIT_TIMEOUT,
                "-A",
                OXO_EGRESS_FILTER_CHAIN,
                "-d",
                target,
                "-j",
                "DROP",
            ]
        )
        if result is None or result.returncode != 0:
            error_msg = (
                result.stderr.decode(errors="ignore")
                if result is not None
                else "command failed"
            )
            logger.warning("Failed to append DROP rule for %s: %s", target, error_msg)
            all_success = False
    return all_success
