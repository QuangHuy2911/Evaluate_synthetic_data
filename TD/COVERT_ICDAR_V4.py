import xml.etree.ElementTree as ET
import xml.dom.minidom

import os
import shutil
import glob

import random

ori_folder = "./TRUOC"
resu_folder = "./SAU"
save_folder = "./Data"

def extract_pascal_voc(filename):
    tree = ET.parse(filename)
    root = tree.getroot()
    tables = []
    for object_elem in root.findall("object"):
        object_name = object_elem.find("name").text
        if object_name == "table":
            bndbox_elem = object_elem.find("bndbox")
            x_min = int(bndbox_elem.find("xmin").text)
            y_min = int(bndbox_elem.find("ymin").text)
            x_max = int(bndbox_elem.find("xmax").text)
            y_max = int(bndbox_elem.find("ymax").text)
            
            tables.append((x_min, y_min, x_max, y_max))
    
    return tables

def create_icdar_xml(filename, tables):
    base_name = os.path.splitext(os.path.basename(filename))[0]
    output_filename_jpg = f"{base_name}.jpg"

    document = ET.Element("document", filename=output_filename_jpg)
    for table_coords in tables:
        table = ET.SubElement(document, "table")
        x_min, y_min, x_max, y_max = table_coords
        coords = ET.SubElement(table, "Coords", points=f"{x_min},{y_min} {x_max},{y_min} {x_max},{y_max} {x_min},{y_max}")
    
    tree = ET.ElementTree(document) 
    output_filename = os.path.join(resu_folder, f"{base_name}.xml")  # Tạo tên tệp mới với phần đuôi "_icdar.xml"
    # tree.write(output_filename, encoding="UTF-8", xml_declaration=True)


    # Ghi tệp XML với định dạng và xuống dòng đúng
    with open(output_filename, "w", encoding="UTF-8") as output_file:
        
        xml_str = ET.tostring(document, encoding="utf-8")
        dom = xml.dom.minidom.parseString(xml_str)
        pretty_xml_str = dom.toprettyxml(indent="  ", encoding="UTF-8").decode("utf-8")
        output_file.write(pretty_xml_str)


if __name__ == "__main__":
    # Copy all jpg file and xml file in folder to output folder
    for jpg_file in glob.iglob(os.path.join(ori_folder, "*.jpg")):
        shutil.copy(jpg_file, resu_folder)

    for file_name in os.listdir(ori_folder):
        if file_name.endswith(".jpg"):
            continue
        ori_filename = os.path.join(ori_folder, file_name)
        tables = extract_pascal_voc(ori_filename)

        # base_name = file_name.split(".")[0]
        create_icdar_xml(ori_filename, tables)

    # Spit data into training, test & test ground truth
    test_folder = os.path.join(save_folder,"./test")
    test_gt_folder = os.path.join(save_folder,"./test_ground_truth")
    train_folder = os.path.join(save_folder,"./train")

    if os.path.exists(test_folder)==False:
        os.mkdir(test_folder)

    if os.path.exists(test_gt_folder)==False:
        os.mkdir(test_gt_folder)

    if os.path.exists(train_folder)==False:
        os.mkdir(train_folder)   

    # shuffle the data
    random.seed(20)
    random.shuffle(os.listdir(resu_folder))

    # Split data:
    size_train = int(len(os.listdir(resu_folder)) * 0.8)
    if size_train % 2 != 0:
        size_train += 1

    for i in range(size_train):
        shutil.copy(os.path.join(resu_folder, os.listdir(resu_folder)[i]), train_folder)
    
    for i in range(size_train, len(os.listdir(resu_folder))):
        shutil.copy(os.path.join(resu_folder, os.listdir(resu_folder)[i]), test_folder)

    for xml_file in glob.iglob(os.path.join(test_folder, "*.xml")):
        shutil.move(xml_file, test_gt_folder)