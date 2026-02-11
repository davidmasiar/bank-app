from django.db import models

class Application(models.Model):
    # Core info
    name = models.CharField(max_length=255)
    domain = models.CharField(max_length=100)
    is_core = models.BooleanField(default=False)
    criticality = models.CharField(max_length=50) # High, Medium, Low 
    lifecycle_status = models.CharField(max_length=50) # Discovery, Active, Decommissioned
    
    # Vlastnictví 
    business_owner = models.CharField(max_length=255)
    it_owner = models.CharField(max_length=255)
    vendor = models.CharField(max_length=255)
    
    # Infrastruktura 
    environments = models.CharField(max_length=255) # DEV/UAT/PROD
    region = models.CharField(max_length=100)
    hosting = models.CharField(max_length=100) # On-prem, Cloud
    
    # Technologie 
    tech_stack = models.TextField()
    database = models.CharField(max_length=255)
    runtime = models.CharField(max_length=255)
    
    # Business a dluh 
    capabilities = models.TextField()
    tech_debt = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Integration(models.Model):
    source = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='outgoing_integrations')
    target = models.ForeignKey('Application', on_delete=models.CASCADE, related_name='incoming_integrations')
    
    INTEGRATION_TYPES = [
        ('API', 'API'),
        ('File', 'File Transfer'),
        ('Message', 'Message Queue'),
    ]
    type = models.CharField(max_length=20, choices=INTEGRATION_TYPES)
    
    direction = models.CharField(max_length=50) # Inbound/Outbound
    volume = models.CharField(max_length=100) 
    
    SENSITIVITY_CHOICES = [
        ('Low', 'Nízká (Veřejná data)'),
        ('Standard', 'Standardní (Interní)'),
        ('High', 'Vysoká (GDPR / Citlivé)'),
    ]
    data_sensitivity = models.CharField(
        max_length=50, 
        choices=SENSITIVITY_CHOICES, 
        default='Standard'
    )

    def __str__(self):
        return f"{self.source.name} -> {self.target.name} ({self.type})"