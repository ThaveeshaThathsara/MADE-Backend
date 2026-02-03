def calculate_priority(importance_kk, required_time_trk, available_time_tak):
    
    print(f"Priority calculation triggered: Kk={importance_kk}, TRk={required_time_trk}, TAk={available_time_tak}")
    
    if available_time_tak <= 0:
        priority = 10.0
        return priority, "Critical Priority (Time Expired)"
        
    priority = importance_kk * (required_time_trk / available_time_tak)
    return round(priority, 4), f"Priority Vk: {round(priority, 4)}"
