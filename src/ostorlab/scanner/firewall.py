"""Firewall management for scan network isolation using iptables."""

import ipaddress
import logging
import subprocess

logger = logging.getLogger(__name__)

OXO_EGRESS_FILTER_CHAIN = "OXO_EGRESS_FILTER"
DOCKER_USER_CHAIN = "DOCKER-USER"
IPTABLES_BIN = "iptables"
IP6TABLES_BIN = "ip6tables"


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
    ip: str,
) -> ipaddress.IPv4Network | ipaddress.IPv6Network | None:
    try:
        return ipaddress.ip_network(ip, strict=False)
    except ValueError:
        logger.warning("Invalid IP address or network: %s", ip)
        return None


def _ensure_chain(binary: str, chain: str) -> bool:
    result = _execute_command([binary, "-N", chain])
    if result is None:
        return False
    if result.returncode == 0:
        return True
    if "already exists" in result.stderr.decode(errors="ignore").lower():
        logger.debug("Chain %s already exists in %s", chain, binary)
        return True
    logger.warning(
        "Failed to create chain %s in %s: %s",
        chain,
        binary,
        result.stderr.decode(errors="ignore"),
    )
    return False


def _ensure_jump_rule(binary: str, parent_chain: str, target_chain: str) -> bool:
    check_result = _execute_command([binary, "-C", parent_chain, "-j", target_chain])
    if check_result is None:
        return False
    if check_result.returncode == 0:
        return True

    insert_result = _execute_command(
        [binary, "-I", parent_chain, "1", "-j", target_chain]
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


def flush_blacklist() -> bool:
    """Flush all rules in OXO_EGRESS_FILTER chain for IPv4 and IPv6."""
    all_success = True
    for binary in (IPTABLES_BIN, IP6TABLES_BIN):
        result = _execute_command([binary, "-F", OXO_EGRESS_FILTER_CHAIN])
        if result is None:
            logger.warning(
                "Could not flush chain %s with %s",
                OXO_EGRESS_FILTER_CHAIN,
                binary,
            )
            all_success = False
        elif result.returncode != 0:
            logger.warning(
                "Chain %s flush returned non-zero with %s: %s",
                OXO_EGRESS_FILTER_CHAIN,
                binary,
                result.stderr.decode(errors="ignore"),
            )
            all_success = False
        else:
            logger.debug(
                "Successfully flushed chain %s in %s",
                OXO_EGRESS_FILTER_CHAIN,
                binary,
            )
    return all_success


def apply_blacklist(ips: list[str]) -> bool:
    """Flush and apply blacklist DROP rules for the given IPs and networks."""
    flush_success = flush_blacklist()
    if not ips:
        return flush_success

    all_success = flush_success
    for ip in ips:
        network = _validate_ip(ip)
        if network is None:
            all_success = False
            continue
        target = (
            str(network.network_address)
            if network.num_addresses == 1 and "/" not in ip
            else str(network)
        )
        if isinstance(network, ipaddress.IPv4Network):
            result = _execute_command(
                [
                    IPTABLES_BIN,
                    "-A",
                    OXO_EGRESS_FILTER_CHAIN,
                    "-d",
                    target,
                    "-j",
                    "DROP",
                ]
            )
        else:
            result = _execute_command(
                [
                    IP6TABLES_BIN,
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
