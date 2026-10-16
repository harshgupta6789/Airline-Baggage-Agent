import logging

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger("airline-claims")

def log_claim_result(
        pnr: str,
        claim_type,
        decision,
        latency: float,
):
    logger.info(
        "claim_result | "
        f"pnr={pnr} | "
        f"claim type={claim_type} | "
        f"decision={decision} | "
        f"latency={latency:.2f}s"
    )