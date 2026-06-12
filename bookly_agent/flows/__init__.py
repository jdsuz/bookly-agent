from bookly_agent.flows.general_faq import GeneralFaqFlow
from bookly_agent.flows.order_status import OrderStatusFlow
from bookly_agent.flows.refund import RefundFlow

FLOW_BY_NAME = {
    "order_status": OrderStatusFlow(),
    "refund": RefundFlow(),
    "general_faq": GeneralFaqFlow(),
}
