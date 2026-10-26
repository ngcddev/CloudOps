# Catálogo de planes centralizado en seed/plans.json (spec 011, T04).
locals {
  plans = {
    for plan in jsondecode(file("${path.module}/../../seed/plans.json")) :
    plan.code => plan
  }
}
