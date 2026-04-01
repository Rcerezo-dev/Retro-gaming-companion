  Skills que te sirven directamente                                                                                           
  /revisar — el más valioso                                    
                                                               
  Lee todos los archivos de src/rom_manager/ y hace exactamente
   lo que el análisis pedía: revisión de calidad. Lo ideal     
  sería correrlo después de cada sesión de cambios importantes 
  antes de dar algo por terminado. Habría detectado los except:
   pass silenciosos, los race conditions en los dicts globales,
   y el rollback incompleto del renamer.

  /simplify — complementario al revisar

  Se activa sobre código que acabas de cambiar (no el proyecto 
  entero) y busca oportunidades de reutilización,
  simplificación y calidad. Úsalo justo después de implementar 
  algo nuevo, por ejemplo cuando arreglemos los locks o        
  refactoricemos server.py.

  /siguiente — para no perderte en el caos

  Con los ~20 issues encontrados, es fácil perder el hilo. Este
   skill lee tus archivos de memoria (phases.md, MEMORY.md) y  
  sugiere qué hacer a continuación según el estado real del    
  proyecto. Útil al inicio de cada sesión.

  /dia — historial de lo que se hizo

  Crea un archivo de diario en Tareas/. Con bugs tan sutiles   
  como los race conditions, tener registro de cuándo y por qué 
  se hizo cada cambio es útil si algo falla en el futuro.      

  ---
  Agentes que te sirven para trabajo pesado

  Plan — antes de tocar server.py

  El archivo tiene 4.400 líneas y la refactorización tiene     
  muchos riesgos. Antes de dividirlo en módulos, usa el agente 
  Plan para que diseñe la estructura sin riesgo de romper nada.

  Explore (en background) — búsquedas amplias

  Ya lo usé para el audit de hoy. Cuando necesites entender el 
  impacto de un cambio en múltiples archivos (ej: "¿todos los  
  sitios donde se actualiza _job_results sin lock?"), lánzalo  
  en background mientras hacemos otra cosa.

  ---
  Lo que NO tienes y sería útil

  - Un agente de tests automáticos — el proyecto no tiene      
  ninguno y los módulos críticos (renamer, scanner, sync) son  
  los más peligrosos de modificar sin red de seguridad.        
  - El skill /sync-design te podría servir si quieres
  replantear la arquitectura de sincronización, pero es más    
  específico.

  ---
  Orden de acción recomendado

  1. /siguiente      → qué priorizar de los 20 issues
  2. Plan agent      → diseñar el fix de los críticos (locks,  
  rollback)
  3. Implementar     → los fixes
  4. /simplify       → revisar lo que se cambió
  5. /revisar        → pase final de calidad
  6. /dia            → registrar la sesión

  ¿Quieres que empecemos por los bugs críticos (race conditions
   y rollback del renamer), o prefieres primero un plan        
  completo?