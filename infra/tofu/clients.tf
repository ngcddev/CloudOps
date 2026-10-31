# Instancia un entorno por cliente usando el inventario y las cuotas del catálogo central (spec 011, T07).
module "client" {
  for_each = var.clients
  source   = "./modules/client-env"

  name = each.key
  host = each.value.host
  plan = each.value.plan
  quota = {
    cpu    = local.plans[each.value.plan].cpu_quota
    memory = local.plans[each.value.plan].memory_quota
  }
  image_name = "plantilla"
}
