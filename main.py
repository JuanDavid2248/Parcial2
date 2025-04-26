import os
import re
from typing import Optional, List

from fastapi import FastAPI, HTTPException, status, BackgroundTasks, Body, Query
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field  # type: ignore



app = FastAPI()

#probar api

@app.get("/")
def read_root():
    return {"message": "API de Calificaciones Activa"}


#modelo studentgrade

class StudentGrade(BaseModel):
    student_id: int
    nombre: str
    materia: str
    calificacion: float = Field(..., ge=0.0, le=5.0)  # Calificación entre 0 y 5
    comentarios: Optional[str] = None

#endpoint #1 - GET /student/{student_id}/report



# Simulación de base de datos en memoria
students_data = [
    StudentGrade(student_id=1, nombre="Juan Pérez", materia="Matemáticas", calificacion=4.5, comentarios="Buen desempeño"),
    StudentGrade(student_id=2, nombre="Laura Gómez", materia="Ciencias", calificacion=3.8),
    StudentGrade(student_id=3, nombre="Carlos Díaz", materia="Historia", calificacion=4.9, comentarios="Excelente análisis"),
]



@app.get("/student/{student_id}/report", response_class=FileResponse)
def get_student_report(student_id: int, background_tasks: BackgroundTasks):
    student = next((s for s in students_data if s.student_id == student_id), None)

    if not student:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Estudiante con ID {student_id} no encontrado."
        )

    report_content = (
        f"Reporte de Calificaciones\n"
        f"==========================\n"
        f"ID: {student.student_id}\n"
        f"Nombre: {student.nombre}\n"
        f"Materia: {student.materia}\n"
        f"Calificación: {student.calificacion}\n"
        f"Comentarios: {student.comentarios or 'N/A'}\n"
    )

    filename = f"reporte_estudiante_{student_id}.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(report_content)

        background_tasks.add_task(os.remove, filename)

        return FileResponse(path=filename, filename=filename, media_type="text/plain")
    
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error al generar el archivo de reporte: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desconocido: {str(e)}"
        )


#endpoint 2



@app.post("/grades/bulk", response_class=FileResponse)
def cargar_calificaciones(background_tasks: BackgroundTasks, grades: List[StudentGrade] = Body(...)):
    if not grades:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Debe proporcionar al menos una calificación."
        )

    students_data.extend(grades)  # Agregamos a la "base de datos"

    reporte = "Reporte de Carga Masiva de Calificaciones\n"
    reporte += "========================================\n"
    for student in grades:
        reporte += (
            f"ID: {student.student_id} | "
            f"Nombre: {student.nombre} | "
            f"Materia: {student.materia} | "
            f"Calificación: {student.calificacion} | "
            f"Comentarios: {student.comentarios or 'N/A'}\n"
        )

    filename = "reporte_carga_masiva.txt"
    try:
        with open(filename, "w", encoding="utf-8") as f:
            f.write(reporte)

        background_tasks.add_task(os.remove, filename)

        return FileResponse(path=filename, filename=filename, media_type="text/plain")
    
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de entrada/salida al generar el reporte de carga masiva: {str(e)}"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error desconocido al generar el reporte: {str(e)}"
        )




#endpoint 3

@app.get("/grades/summary")
def get_grades_summary(
    background_tasks: BackgroundTasks,
    calificacion_minima: float = Query(None, description="Filtrar calificaciones mayores o iguales"),
    materia: str = Query(None, description="Filtrar por materia"),
    formato: str = Query("json", pattern=re.compile("^(json|txt)$"), description="Formato de respuesta: json o txt"),
):
    estudiantes_filtrados = students_data

    if calificacion_minima is not None:
        estudiantes_filtrados = [s for s in estudiantes_filtrados if s.calificacion >= calificacion_minima]

    if materia is not None:
        estudiantes_filtrados = [s for s in estudiantes_filtrados if s.materia.lower() == materia.lower()]

    if not estudiantes_filtrados:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No hay estudiantes que cumplan con los filtros especificados."
        )

    try:
        total_calificaciones = sum(s.calificacion for s in estudiantes_filtrados)
        promedio_calificaciones = total_calificaciones / len(estudiantes_filtrados)
    except ZeroDivisionError:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error: División por cero al calcular el promedio."
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al calcular el resumen: {str(e)}"
        )

    if formato == "json":
        return {
            "total_calificaciones": total_calificaciones,
            "promedio_calificaciones": promedio_calificaciones,
            "cantidad_estudiantes": len(estudiantes_filtrados)
        }

    try:
        reporte = "Resumen de Calificaciones Filtradas\n"
        reporte += "=================================\n"
        for s in estudiantes_filtrados:
            reporte += (
                f"ID: {s.student_id} | Nombre: {s.nombre} | "
                f"Materia: {s.materia} | Calificación: {s.calificacion} | "
                f"Comentarios: {s.comentarios or 'N/A'}\n"
            )
        reporte += f"\nPromedio: {promedio_calificaciones:.2f}\n"
        reporte += f"Total calificaciones: {total_calificaciones}\n"

        filename = "resumen_filtrado.txt"
        with open(filename, "w", encoding="utf-8") as f:
            f.write(reporte)

        background_tasks.add_task(os.remove, filename)

        return FileResponse(path=filename, filename=filename, media_type="text/plain")
    
    except IOError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error de entrada/salida al generar el resumen: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error inesperado al generar el resumen: {str(e)}"
        )


