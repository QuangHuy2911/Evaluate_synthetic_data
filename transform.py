import xml.etree.ElementTree as ET
import os

list_no_use = ["table column header"]

def create_ground_truth(root, cell_name, cell_bboxs, cell_corners, cell_location, cell_table_id): 
    obj = ET.SubElement(root, 'object')
    ET.SubElement(obj, 'name').text = cell_name
    ET.SubElement(obj, 'difficult').text = '0'
    # Create bounding box
    bndbox = ET.SubElement(obj, 'bndbox')
    ET.SubElement(bndbox, 'xmin').text = str(float(cell_bboxs[0]))
    ET.SubElement(bndbox, 'ymin').text = str(float(cell_bboxs[1]))
    ET.SubElement(bndbox, 'xmax').text = str(float(cell_bboxs[2]))
    ET.SubElement(bndbox, 'ymax').text = str(float(cell_bboxs[3]))
    # Create cell corners
    ET.SubElement(bndbox, 'x1').text = str(float(cell_corners[0]))
    ET.SubElement(bndbox, 'y1').text = str(float(cell_corners[1]))
    ET.SubElement(bndbox, 'x2').text = str(float(cell_corners[2]))
    ET.SubElement(bndbox, 'y2').text = str(float(cell_corners[3]))
    ET.SubElement(bndbox, 'x3').text = str(float(cell_corners[4]))
    ET.SubElement(bndbox, 'y3').text = str(float(cell_corners[5]))
    ET.SubElement(bndbox, 'x4').text = str(float(cell_corners[6]))
    ET.SubElement(bndbox, 'y4').text = str(float(cell_corners[7]))
    # Create cell location
    ET.SubElement(bndbox, 'start_col').text = str(cell_location[0][0])
    ET.SubElement(bndbox, 'end_col').text = str(cell_location[1][0])
    ET.SubElement(bndbox, 'start_row').text = str(cell_location[2][0])
    ET.SubElement(bndbox, 'end_row').text = str(cell_location[3][0])
    ET.SubElement(bndbox, 'table_id').text = str(cell_table_id)

# Save the table, table row, table column and table spanning cell in the dictionary
def save_rows_columns_span_cells_for_each_table(root, object):
    # Save all the tables
    table_id = 0
    for elem in root.findall('./object'):
        name = elem.find('name').text
        if name != 'table':
            continue
        else:
            object[table_id] = dict()
            xmin = int(elem.find('./bndbox/xmin').text)
            ymin = int(elem.find('./bndbox/ymin').text)
            xmax = int(elem.find('./bndbox/xmax').text)
            ymax = int(elem.find('./bndbox/ymax').text)
            if object[table_id] == {}:
                object[table_id][name] = []
            object[table_id][name].append([xmin, ymin, xmax, ymax])
            table_id += 1
        
    # Give each element in the table a table id & count
    for elem in root.findall('./object'):
        name = elem.find('name').text
        if name == 'table' or name in list_no_use:
            continue
        xmin = int(elem.find('./bndbox/xmin').text)
        ymin = int(elem.find('./bndbox/ymin').text)
        xmax = int(elem.find('./bndbox/xmax').text)
        ymax = int(elem.find('./bndbox/ymax').text)
        for table_id in object.keys():
            if object[table_id]['table'][0][0] <= xmin and object[table_id]['table'][0][2] >= xmax and object[table_id]['table'][0][1] <= ymin and object[table_id]['table'][0][3] >= ymax:
                if name not in object[table_id].keys():
                    object[table_id][name] = []
                    count = 0
                else:
                    count = (object[table_id][name][-1][0][0] + 1)
                object[table_id][name].append([[count], [xmin, ymin, xmax, ymax]])

# Delete remove all object from the root
def delete_all_unwanted_obj(root):
    for elem in root.findall('./object'):
        root.remove(elem)
    for elem in root.findall('./path'):
        root.remove(elem)
    for elem in root.findall('./source'):
        root.remove(elem)
    

# Create cells from row and column from dictionary 
def create_cells_from_row_and_column(object):
    cells = list()
    for table_id in object.keys():
        for row in object[table_id]['table row']:
            for col in object[table_id]['table column']: 
                cell_xmin = col[-1][0]
                cell_ymin = row[-1][1]
                cell_xmax = col[-1][2]
                cell_ymax = row[-1][3]
                cell_startcol = col[0]
                cell_endcol = col[0] 
                cell_startrow = row[0]
                cell_endrow = row[0]
                cell_bboxs = [cell_xmin, cell_ymin, cell_xmax, cell_ymax]
                cell_corners = [cell_xmin, cell_ymin, cell_xmax, cell_ymin, cell_xmax, cell_ymax, cell_xmin, cell_ymax]
                cell_location = [cell_startcol, cell_endcol, cell_startrow, cell_endrow]
                cells.append([['box'], cell_bboxs, cell_corners, cell_location, table_id])
    return cells


# Handle with spanning cell
def handle_spanning_cell(object, cells):
    span_cell = dict()
    count = 0
    indices = list()
    for table_id in object.keys():
        span_cell[table_id] = dict()
        # Give each span cell a table id & index
        if 'table spanning cell' not in object[table_id].keys():
            continue
        for elem in object[table_id]['table spanning cell']:
            span_count = list()
            for index, grid in enumerate(cells):
                if (grid[1][0] >= elem[1][0] and grid[1][0] <= elem[1][2]
                    and grid[1][1] >= elem[1][1] and grid[1][1] <= elem[1][3]
                    and grid[1][2] >= elem[1][0] and grid[1][2] <= elem[1][2]
                    and grid[1][3] >= elem[1][1] and grid[1][3] <= elem[1][3]):
                    span_count.append(grid)
                    indices.append(index)
            span_cell[table_id][count] = span_count
            count += 1

    # Cells are not spanning cell
    cells = [cell for cell in cells if cells.index(cell) not in indices]

    # Create new cells for spanning cell
    for i in range(len(span_cell.keys())):
        for key in span_cell[i].keys():
            list_cells = span_cell[i][key]
            xmin_list = list()
            ymin_list = list()
            xmax_list = list()
            ymax_list = list()
            startcol_cell = list()
            endcol_cell = list()
            startrow_cell = list()
            endrow_cell = list()
            for cell in list_cells:
                xmin_list.append(cell[1][0])
                ymin_list.append(cell[1][1])
                xmax_list.append(cell[1][2])
                ymax_list.append(cell[1][3])
                startcol_cell.append(cell[3][0])
                endcol_cell.append(cell[3][1])
                startrow_cell.append(cell[3][2])
                endrow_cell.append(cell[3][3])
            xmin = min(xmin_list)
            ymin = min(ymin_list)
            xmax = max(xmax_list)
            ymax = max(ymax_list)
            startcol_cell = min(startcol_cell)
            endcol_cell = max(endcol_cell)
            startrow_cell = min(startrow_cell)
            endrow_cell = max(endrow_cell)
            cells.append([['box'], [xmin, ymin, xmax, ymax], [xmin, ymin, xmax, ymin, xmax, ymax, xmin, ymax], [startcol_cell, endcol_cell, startrow_cell, endrow_cell], i])
    
    return cells
def create_new_object(root, cells):
# Create a new object for each cell
    for cell in cells:
        create_ground_truth(root, cell[0][0], cell[1], cell[2], cell[3], cell[4])

# Create a new file for new root
def create_new_ground_truth(root, output, file_xml):
    tree = ET.ElementTree(root)
    ET.indent(tree)
    save_file = os.path.join(output, file_xml)
    tree.write(save_file)

if __name__ == '__main__':
    input_folder = './results'
    output_folder = './samples'
    for file in os.listdir(input_folder):
        if file.endswith('.xml'):
            tree = ET.parse(os.path.join(input_folder, file))
            root = tree.getroot()
            object = dict()
            save_rows_columns_span_cells_for_each_table(root, object)
            delete_all_unwanted_obj(root)
            cells = create_cells_from_row_and_column(object)
            for table_id in object.keys():
                if "table spanning cell" in object[table_id].keys():
                   cells = handle_spanning_cell(object, cells)
            create_new_object(root, cells)
            create_new_ground_truth(root, output_folder, file)
            

        


