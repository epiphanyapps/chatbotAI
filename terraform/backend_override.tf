# Temporary local backend - will migrate to remote later
terraform {
  backend "local" {
    path = "terraform.tfstate"
  }
}
