## 1. Objetivo

Entrenar un modelo de detección de objetos capaz de identificar:

- Personas
- Skates 

Para aportar mas datasets (archivos .txt) de coordenadas bounding boxes sobre los objetos identificados. Además de visuales para la respresentacion de la direccion de arte.

## 2. Dataset

### 2.1 Captura de imágenes

Se recopilaron 15 fotografías donde aparecen:

- Personas en diferentes poses
- Skates en distintas orientaciones
- Escenas urbanas reales

Criterios de selección:

- Variación de escala (cerca / lejos)
- Diferentes fondos
- Occlusiones parciales
- Distintas condiciones de luz

<img width="1723" height="647" alt="IMFOLDER" src="https://github.com/user-attachments/assets/4173e30d-03f4-4aaa-a21d-d5bd19a43ee2" />


## 3. Anotación manual con Label Studio

Para garantizar calidad en un dataset pequeño, se realizó **anotación manual precisa bounding box a bounding box** usando ***Label Studio***. En anaconda prompt:

	pip install label-studio
	label-studio

### 3.2 Proceso de anotación

Para cada imagen:

1. Abrir imagen en Label Studio
2. Dibujar bounding box alrededor del objeto
3. Asignar clase correcta:
    - `persona`
    - `skate`
4. Ajustar con precisión los bordes
5. Guardar anotación

Se anotaron manualmente:

- Todas las personas visibles
- Todos los skates visibles
- Incluso objetos parcialmente visibles

Esto generó un dataset **muy limpio y consistente** pese al tamaño reducido.

<img width="1872" height="911" alt="LABELSTUDIO" src="https://github.com/user-attachments/assets/78f6c280-6cf5-4f74-a8bf-7381d9a8e624" />


### 3.3 Exportación en formato YOLO

Las anotaciones se exportaron en:

	YOLO format

	dataset/
	 ├── images/
	 │    ├── img1.jpg
	 │    ├── img2.jpg
	 │    └── ...
	 ├── labels/
	 │    ├── img1.txt
	 │    ├── img2.txt
	 │    └── ...

Formato del label (archivo output .txt coordenadas bounding box detectado): 

	class x_center y_center width height



## 4. Entrenamiento con YOLO

Se utilizó:
- Ultralytics YOLO

		pip install ultralytics

Repositorio oficial:
- [https://github.com/ultralytics/ultralytics](https://github.com/ultralytics/ultralytics)

Se consigue un modelo entrenado que nos muestra las imagenes usadas

![TRAINBATCH](https://github.com/user-attachments/assets/881e7838-68bd-4e9a-bdae-01004f1020ad)



## 5. Modelo de prediccion final

Archivo .yaml

	path: dataset  
	train: images  
	val: images  
	  
	names:  
	0: persona  
	1: skate


Archivo python

	from ultralytics import YOLO
	
	  
	
	def main():
	
	    model = YOLO("newmodel.pt")
	
	    model.predict(source = "mi_video.mp4", show=True, save=True, conf=0.1, line_width=2, save_crop = False, save_txt = False, classes = [0,1])
	
	  
	
	if __name__ == "__main__":
	
	    main()


Con esto, se obtendrá un archivo .avi con el video output con la deteccion predict de skates y personas.



https://github.com/user-attachments/assets/d3457221-1f0d-4846-a335-5bc5163cd3c9



## 6. Dataset final

Finalmente, se puede seleccionar una libreria de imagenes del Macba, para extraer datos estadísticos sobre el conteo de personas y skates en imagenes publicadas. Incluso se podria a tiempo real, mediante un hardware especifico, la deteccion en directo de personas y skates que se encuentran en la plaza. 
