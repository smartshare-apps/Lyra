from flask import render_template

# data visualisation modules (bokeh)
from bokeh.plotting import figure
from bokeh.embed import components

# ecomm module imports
import database.config as config
from database.product import *
import database.resources as resources
import database.order as order
import database.store as store
import database.customer as customer
import database.plugins as plugins
import database.shipment as shipment
import database.dashboard as dashboard
import database.vendor as vendor
import database.message as message

from database.product_util import *
from database.order_util import *
from database.dashboard_util import *

from db import *

import sys, ast, imp

ERROR_CODES = config.ERROR_CODES


class ControlPanel(object):
    def __init__(self):
        self.setupVariables()

    def setupVariables(self, ):
        self.control_data = {}

    def render_tab(self, tab, data=None):
        instance_db = instance_handle()
        self.instance_db = instance_db.cursor()

        if type(data) != list and data in config.ERROR_CODES:
            return self.settings_Advanced(flag=data)

        store_db = db_handle(instance_db)

        if store_db is None and tab != "settings_advanced":
            return "NO_DB"
        elif store_db is None and tab == "settings_advanced":
            return self.settings_Advanced(flag="NO_DB")
        else:
            self.database = store_db.cursor()

        # products section
        if tab == "products":
            return self.product_Main()
        elif tab == "product_inventory":
            return self.product_Inventory()
        elif tab == "product_editor":
            return self.product_ProductEditor(data)
        elif tab == "product_bulk_editor":
            return self.product_BulkProductEditor(data)
        elif tab == "product_inventory_editor":
            return self.product_InventoryEditor(data)
        elif tab == "product_bulk_inventory_editor":
            return self.product_BulkInventoryEditor(data)
        elif tab == "product_collections":
            return self.product_Collections()
        elif tab == "collection_editor":
            return self.product_CollectionEditor(data)
        elif tab == "product_bulk_collection_editor":
            return self.product_BulkCollectionEditor(data)


        # orders section
        elif tab == "orders":
            return self.order_Main()
        elif tab == "orders_drafts":
            return self.order_Drafts()
        elif tab == "order_editor":
            return self.order_OrderEditor(data)
        elif tab == "order_editor_draft_new":
            return self.order_addDraft()
        elif tab == "order_fulfill":
            return self.order_FulfillOrder(data)


        # customers section
        elif tab == "customers":
            return self.customer_Main()
        elif tab == "customer_editor":
            return self.customer_CustomerEditor(data)


        # settings section
        elif tab == "settings":
            return self.settings_Main()
        elif tab == "settings_payment":
            return self.settings_Payment()
        elif tab == "settings_shipping":
            return self.settings_Shipping()
        elif tab == "settings_advanced":
            return self.settings_Advanced()


        # store settings section
        elif tab == "store_settings":
            return self.store_settings_Main()
        elif tab == "store_settings_navigation":
            return self.store_settings_Navigation()
        elif tab == "store_settings_footer":
            return self.store_settings_Footer()
        elif tab == "store_settings_pages":
            return self.store_settings_Pages()
        elif tab == "store_settings_page_editor":
            return self.store_settings_PageEditor(data)
        elif tab == "store_settings_file_manager":
            return self.store_settings_FileManager()
        elif tab == "store_settings_theme_manager":
            return self.store_settings_ThemeManager()
        elif tab == "store_settings_analytics":
            return self.store_settings_Analytics()

        elif tab == "plugins":
            return self.plugins_Main()
        elif tab == "plugins_pyutil":
            return self.plugins_PyUtil(data)

        elif tab == "dashboard":
            return self.dashboard_Main()
        elif tab == "dashboard_live_chat":
            return self.dashboard_LiveChat()

        self.database = None
        db.close()

    def product_Main(self):
        self.control_data["page"] = "products"
        self.control_data["productMainTable"] = self.product_MainTable()
        self.control_data["productActionPanel"] = self.product_MainActionPanel()
        self.control_data["productSearchPanel"] = self.product_SearchPanel()
        self.control_data["modals"] = [render_template("control_panel/product/modal_add_product.html"),
                                       render_template("control_panel/product/modal_update_inventory.html")]

        return render_template("control_panel/product/Main.html", control_data=self.control_data)

    def product_Inventory(self):
        self.control_data["page"] = "product_inventory"
        self.control_data["productInventoryTable"] = self.product_InventoryTable()
        self.control_data["productInventoryActionPanel"] = self.product_InventoryActionPanel()
        self.control_data["productSearchPanel"] = self.product_SearchPanel()
        return render_template("control_panel/product/Inventory.html", control_data=self.control_data)

    def product_Collections(self):
        self.control_data["page"] = "product_collections"
        self.control_data["productCollectionTable"] = self.product_CollectionTable()
        self.control_data["productCollectionActionPanel"] = self.product_CollectionActionPanel()
        self.control_data["productSearchPanel"] = self.product_SearchPanel()

        self.control_data["modals"] = [render_template("control_panel/product/modal_add_collection.html")]

        return render_template("control_panel/product/Collections.html", control_data=self.control_data)

    def product_ProductEditor(self, product_id):
        self.control_data["page"] = "product_editor"
        self.control_data["product_id"] = product_id
        self.control_data["product_types"] = config.loadProductTypes(self.instance_db);
        self.control_data["product_vendors"] = vendor.loadAllVendors(self.database);

        # pull product types from settings table for updating product type dropdown selection

        productData = loadProduct(product_id, self.database)
        self.control_data["stripe_data"] = stripe_manager.getProduct(productData)
        self.control_data["default_variant_data"] = stripe_manager.getDefaultVariant(productData)

        if productData["Tags"]:
            productData["Tags"] = formatProductTags(productData["Tags"])
        else:
            productData["Tags"] = []

        # gets image resource id list from resource database
        if productData.has_key("resources"):
            if (productData["resources"] is not None and productData["resources"] != ""):
                imageResources = extractImageResources(productData["resources"])

                # if this product has any image resources, extract the URIs for each of them
                imageURI = resources.loadResourceURIList(imageResources, self.database)
                imageURI = formatImageURIs(imageURI)
                self.control_data[
                    "image_resources"] = imageURI  # so the product editor can access those image resources
            else:
                self.control_data["image_resources"] = {"1": resources.loadResourceURI("1", self.database)}

        variantIDList = findProductVariants(product_id, self.database)

        # load and store product variant data
        self.control_data["variant_product_data"] = []
        productVariants = []

        self.control_data["variant_thumbnails"] = {}
        if variantIDList:
            for variant_id in variantIDList:
                currentVariantProductData = loadProductVariant(variant_id, self.database)
                currentVariantProductData["VariantData"] = formatVariantData(currentVariantProductData["VariantData"])

                currentVariantThumbnail = resources.loadResourceURI(currentVariantProductData["VariantImg"],
                                                                    self.database)

                self.control_data["variant_thumbnails"][str(variant_id)] = currentVariantThumbnail
                self.control_data["variant_product_data"].append(currentVariantProductData)

                productVariants.append(currentVariantProductData)

        # set root product data for template rendering
        self.control_data["product_data"] = productData
        self.control_data["variant_types"] = {}

        variantTypes = productData["VariantTypes"]

        if variantTypes:
            variantTypes = filter(lambda v: v != '', variantTypes.split(';'))

            formattedVariantTypes = {}
            for variant in variantTypes:
                variant = variant.split(':')

                variantType = variant[0]
                variantValues = variant[1].split(',')

                formattedVariantTypes[variantType] = variantValues

            self.control_data["variant_types"] = formattedVariantTypes

        self.control_data["productVariantTable"] = render_template(
            "control_panel/product/productEditor_variantTable.html", productVariants=productVariants,
            variant_thumbnails=self.control_data["variant_thumbnails"])

        return render_template("control_panel/product/productEditor_product.html", control_data=self.control_data)

    def product_CollectionEditor(self, collection_id):
        self.control_data["page"] = "collection_editor"
        self.control_data["collection_id"] = collection_id

        collectionData = loadCollection(collection_id, self.database)
        collectionData["Conditions"] = parseCollectionConditions(collectionData["Conditions"])

        # productIDList = loadProductsInCollection(collectionData["Conditions"], collectionData["Strict"], self.database)

        # if len(productIDList) > 0:
        #	products = loadProductsByID(productIDList, self.database)
        #	print "Here are the products: ", products


        self.control_data["collectionProductsTable"] = render_template(
            "control_panel/product/productEditor_productsInCollection.html")

        self.control_data["collection_data"] = collectionData

        self.control_data["product_tags"] = config.loadProductTags(self.instance_db)
        self.control_data["product_types"] = config.loadProductTypes(self.instance_db)

        collection_image_src = resources.loadResourceURI(collectionData["CollectionImageSrc"], self.database)

        if collection_image_src == None:
            collection_image_src = resources.loadResourceURI("1", self.database)

        self.control_data["collection_image_src"] = collection_image_src

        self.control_data["modals"] = []

        return render_template("control_panel/product/productEditor_collection.html", control_data=self.control_data)

    def product_InventoryEditor(self, variant_id):
        self.control_data["page"] = "product_editor"

        variantData = loadProductVariant(variant_id, self.database)
        variantData["VariantData"] = formatVariantData(variantData["VariantData"])
        product_id = variantData["product_id"]

        self.control_data["product_id"] = product_id

        variantIDList = findProductVariants(product_id, self.database)

        # load and store product variant data
        self.control_data["variant_product_data"] = []
        productVariants = []

        self.control_data["variant_thumbnails"] = {}
        if variantIDList:

            for variant_id in variantIDList:
                currentVariantProductData = loadProductVariant(variant_id, self.database)
                currentVariantProductData["VariantData"] = formatVariantData(currentVariantProductData["VariantData"])

                currentVariantThumbnail = resources.loadResourceURI(currentVariantProductData["VariantImg"],
                                                                    self.database)

                self.control_data["variant_thumbnails"][str(variant_id)] = currentVariantThumbnail
                self.control_data["variant_product_data"].append(currentVariantProductData)

                productVariants.append(currentVariantProductData)

        # set root product data for template rendering
        self.control_data["product_data"] = loadProduct(product_id, self.database)
        self.control_data["variant_data"] = variantData

        self.control_data["productVariantTable"] = render_template(
            "control_panel/product/productEditor_variantTable.html", productVariants=productVariants,
            variant_thumbnails=self.control_data["variant_thumbnails"])

        return render_template("control_panel/product/productEditor_inventory.html", control_data=self.control_data)

    def product_BulkInventoryEditor(self, variantIDList):
        self.control_data["page"] = "product_bulk_inventory_editor"

        # load and store product variant data
        self.control_data["product_data"] = []
        variants = []

        for variant_id in variantIDList:
            currentProductData = loadProduct(variant_id, self.database)  # load each default product
            variants.append(currentProductData)
            self.control_data["product_data"].append(currentProductData)

        selectedFields = config.BulkInventoryEditorSettings(self.instance_db)  # grab user settings for bulk editor
        selectedFields = sorted(selectedFields.split(','))
        self.control_data["selectedFields"] = selectedFields

        # render editable product table based on bulk inventory editor product settings
        selectedFieldsDict = {}
        for i in range(len(selectedFields)):
            selectedFieldsDict[selectedFields[i]] = selectedFields[i]

        self.control_data["modal"] = render_template("control_panel/product/modal_bulkInventoryEditor.html",
                                                     selectedFields=selectedFieldsDict)
        self.control_data["inventoryTable"] = render_template("control_panel/product/productEditor_inventoryTable.html",
                                                              variants=variants, selectedFields=selectedFields)

        return render_template("control_panel/product/productEditor_bulkInventory.html", control_data=self.control_data)

    def product_BulkProductEditor(self, productIDList):
        self.control_data["page"] = "product_bulk_inventory_editor"
        self.control_data["productIDList"] = productIDList

        # load and store product variant data

        products = []

        for i in range(len(productIDList)):
            currentProductData = loadProduct(productIDList[i], self.database)  # load each default product
            currentVariantIDList = findProductVariants(productIDList[i], self.database)  # find it's variants

            products.append([currentProductData])

            if currentVariantIDList:
                for j in range(len(currentVariantIDList)):  # load the data for each product variant
                    currentVariantProductData = loadProductVariant(currentVariantIDList[j], self.database)
                    currentVariantProductData["VariantData"] = formatVariantData(
                        currentVariantProductData["VariantData"])
                    products[i].append(currentVariantProductData)

        self.control_data["product_data"] = products

        selectedFields = config.BulkProductEditorSettings(self.instance_db)  # grab user settings for bulk editor
        selectedFields = sorted(selectedFields.split(','))

        self.control_data["selectedFields"] = selectedFields

        # render editable product table based on bulk editor product settings
        selectedFieldsDict = {}
        for field in selectedFields:
            selectedFieldsDict[field] = field

        self.control_data["modal"] = render_template("control_panel/product/modal_bulkProductEditor.html",
                                                     selectedFields=selectedFieldsDict)
        self.control_data["productTable"] = render_template("control_panel/product/productEditor_productTable.html",
                                                            products=products, selectedFields=selectedFields)

        return render_template("control_panel/product/productEditor_bulkProduct.html", control_data=self.control_data)

    def product_BulkCollectionEditor(self, collectionIDList):
        self.control_data["page"] = "product_bulk_collection_editor"
        self.control_data["collectionIDList"] = collectionIDList

        # load and store product variant data
        collections = []
        collection_thumbnail = {}

        for collection_id in collectionIDList:
            currentCollectionData = loadCollection(collection_id, self.database)  # load each colleciton

            collection_image_src = resources.loadResourceURI(currentCollectionData["CollectionImageSrc"], self.database)
            if collection_image_src == None:
                collection_image_src = resources.loadResourceURI("1", self.database)

            collection_thumbnail[currentCollectionData["collection_id"]] = collection_image_src
            collections.append(currentCollectionData)

        self.control_data["collection_data"] = collections

        selectedFields = config.BulkCollectionEditorSettings(self.instance_db)  # grab user settings for bulk editor
        selectedFields = sorted(selectedFields.split(','))
        self.control_data["selectedFields"] = selectedFields

        # render editable product table based on bulk inventory editor product settings
        selectedFieldsDict = {}
        for field in selectedFields:
            selectedFieldsDict[field] = field

        self.control_data["modal"] = render_template("control_panel/product/modal_bulkCollectionEditor.html",
                                                     selectedFields=selectedFieldsDict)
        self.control_data["collectionTable"] = render_template(
            "control_panel/product/productEditor_collectionTable.html", collections=collections,
            selectedFields=selectedFields, collection_thumbnail=collection_thumbnail)

        return render_template("control_panel/product/productEditor_bulkCollection.html",
                               control_data=self.control_data)

    # panels and misc.
    def product_SearchPanel(self):
        return render_template("control_panel/product/SearchPanel.html", control_data=self.control_data)

    def product_MainActionPanel(self):
        return render_template("control_panel/product/ActionPanel.html", control_data=self.control_data)

    def product_InventoryActionPanel(self):
        return render_template("control_panel/product/InventoryActionPanel.html", control_data=self.control_data)

    def product_CollectionActionPanel(self):
        return render_template("control_panel/product/CollectionActionPanel.html", control_data=self.control_data)

    def product_MainTable(self):
        formattedProductList = loadAllProducts(self.database)
        allVendors = vendor.loadAllVendors(self.database)
        product_thumbnail = {}

        for product_id, product in formattedProductList.iteritems():
            imageURI = resources.loadResourceURI(product["ImageSrc"], self.database)
            product_thumbnail[product_id] = imageURI

        table = render_template("control_panel/product/MainTable.html", productList=formattedProductList,
                                product_thumbnail=product_thumbnail, vendors=allVendors)
        return table

    def product_InventoryTable(self):
        selectedColumns = ["product_id", "ImageSrc"]
        formattedProductList = loadAllProducts(self.database)

        formattedVariantList = loadAllProductVariants(formattedProductList, self.database)

        product_thumbnail = {}
        variant_thumbnails = {}

        for product_id, product in formattedProductList.iteritems():
            imageURI = resources.loadResourceURI(product["ImageSrc"], self.database)
            product_thumbnail[product_id] = imageURI

        for product_id, variants in formattedVariantList.iteritems():
            for variant in variants:
                variant_id = variant["variant_id"]
                variant["VariantData"] = formatVariantData(variant["VariantData"])
                variant_thumbnails[variant_id] = loadResourceURI(int(variant["VariantImg"]), self.database)

        table = render_template("control_panel/product/InventoryTable.html", productList=formattedProductList,
                                variantList=formattedVariantList, product_thumbnail=product_thumbnail,
                                variant_thumbnails=variant_thumbnails)
        return table

    def product_CollectionTable(self):
        collectionList = loadCollections(self.database)
        collection_thumbnail = {}

        if type(collectionList) != type(None):
            for idx, collection in enumerate(collectionList):
                collectionList[idx]["Conditions"] = parseCollectionConditions(collection["Conditions"])
                collection_image_src = resources.loadResourceURI(collection["CollectionImageSrc"], self.database)

                if collection_image_src == None:
                    collection_image_src = resources.loadResourceURI("1", self.database)

                collection_thumbnail[collection["collection_id"]] = collection_image_src

        table = render_template("control_panel/product/CollectionTable.html", collectionList=collectionList,
                                collection_thumbnail=collection_thumbnail)
        return table

    # deprecated
    def updateProducts(self):
        db = db_handle()
        self.database = db.cursor()

        productList = importProductsFromCSV("products_export.csv", "products", self.database)
        insertProducts(productList)

        self.database = None
        db.commit()
        db.close()

    # order section methods
    def order_Main(self):
        self.control_data["page"] = "orders"

        allOrders = order.loadAllOrders(self.database)
        openOrders = {}
        unfulfilledOrders = {}
        unpaidOrders = {}

        if (allOrders):
            openOrders = {order_id: order for order_id, order in allOrders.iteritems() if
                          order["FulfillmentStatus"] != 'fulfilled'}
            unfulfilledOrders = {order_id: order for order_id, order in allOrders.iteritems() if
                                 order["FulfillmentStatus"] != 'fulfilled'}
            unpaidOrders = {order_id: order for order_id, order in allOrders.iteritems() if
                            order["PaymentStatus"] == 'unpaid' or order["PaymentStatus"] == 'pending'}

        self.control_data["table_allOrders"] = render_template("control_panel/order/table_allOrders.html",
                                                               allOrders=allOrders)
        self.control_data["table_openOrders"] = render_template("control_panel/order/table_openOrders.html",
                                                                openOrders=openOrders)
        self.control_data["table_unfulfilledOrders"] = render_template(
            "control_panel/order/table_unfulfilledOrders.html", unfulfilledOrders=unfulfilledOrders)
        self.control_data["table_unpaidOrders"] = render_template("control_panel/order/table_unpaidOrders.html",
                                                                  unpaidOrders=unpaidOrders)

        self.control_data["orderSearchPanel"] = self.order_SearchPanel()
        self.control_data["orderActionPanel"] = self.order_MainActionPanel()

        return render_template("control_panel/order/Main.html", control_data=self.control_data)

    def order_Drafts(self):
        self.control_data["page"] = "orders_drafts"
        allDrafts = loadAllDraftOrders(self.database)

        self.control_data["table_allDrafts"] = render_template("control_panel/order/table_allDrafts.html",
                                                               allDrafts=allDrafts)
        return render_template("control_panel/order/Drafts.html", control_data=self.control_data)

    def order_OrderEditor(self, order_id):
        self.control_data["page"] = "order_editor"
        self.control_data["order_id"] = order_id

        orderData = loadOrder(order_id, self.database)
        customerData = loadCustomer(orderData["customer_id"], self.database)

        # load the products in this order
        products = order.loadOrderProducts(orderData["SKU_List"], self.database)

        product_thumbnails = {}
        for product_id, product in products.iteritems():
            imageURI = resources.loadResourceURI(product["ImageSrc"], self.database)
            product_thumbnails[product_id] = imageURI

        subtotals = {product["VariantSKU"]: int(product["quantity"]) * float(product["VariantPrice"]) for
                     product_id, product in products.iteritems()}

        if orderData["OrderEvents"]:
            orderEventList = orderData["OrderEvents"].split(',')
            timeline = loadEvents(orderEventList, self.database)  # grab raw event data
            timeline = formatOrderTimeline(timeline)  # format it for the timeline template
            self.control_data["order_timeline"] = render_template("control_panel/order/orderTimeline.html",
                                                                  timeline=timeline)

        self.control_data["order_editor_modals"] = render_template("control_panel/order/modal_orderEditor.html",
                                                                   customer_data=customerData, order_data=orderData)
        self.control_data["table_orderProducts"] = render_template("control_panel/order/table_orderProducts.html",
                                                                   products=products,
                                                                   product_thumbnails=product_thumbnails,
                                                                   subtotals=subtotals)
        self.control_data["customer_data"] = customerData
        self.control_data["order_data"] = orderData
        self.control_data["product_data"] = products

        return render_template("control_panel/order/OrderEditor.html", control_data=self.control_data)

    def order_addDraft(self):
        formattedProductList = loadAllProducts(self.database)
        self.control_data["products"] = formattedProductList
        self.control_data["page"] = "order_editor_draft_new"
        return render_template("control_panel/order/OrderEditor_addDraft.html", control_data=self.control_data)

    def order_FulfillOrder(self, order_id):
        self.control_data["page"] = "order_fulfill"
        self.control_data["order_id"] = order_id

        defaultShippingAddressFrom = config.getDefaultShippingAddress(self.instance_db)

        orderData = order.loadOrder(order_id, self.database)
        customerData = loadCustomer(orderData["customer_id"], self.database)

        # load the products in this order
        products = order.loadOrderProducts(orderData["SKU_List"], self.database)

        # loads the shipping information for products in this order
        shipping_data = shipment.loadOrderShipments(order_id, self.database)

        product_thumbnails = {}

        for product_id, product in products.iteritems():
            imageURI = resources.loadResourceURI(product["ImageSrc"], self.database)
            product_thumbnails[product_id] = imageURI

        subtotals = {product["VariantSKU"]: int(product["quantity"]) * float(product["VariantPrice"]) for
                     product_id, product in products.iteritems()}

        self.control_data["table_orderProducts"] = render_template(
            "control_panel/order/table_orderProducts_fulfillment.html", products=products,
            product_thumbnails=product_thumbnails, subtotals=subtotals)
        self.control_data["fulfillment_editor_modals"] = [
            render_template("control_panel/order/modal_createShipment.html"),
            render_template("control_panel/order/modal_fulfillmentEditor.html", customer_data=customerData,
                            order_data=orderData)]

        self.control_data["customer_data"] = customerData
        self.control_data["order_data"] = orderData
        self.control_data["product_data"] = products

        self.control_data["shipping_data"] = shipping_data
        self.control_data["shipping_address_from"] = defaultShippingAddressFrom

        return render_template("control_panel/order/FulfillOrder.html", control_data=self.control_data)

    # panels and misc.
    def order_SearchPanel(self):
        return render_template("control_panel/order/SearchPanel.html", control_data=self.control_data)

    def order_MainActionPanel(self):
        return render_template("control_panel/order/ActionPanel.html", control_data=self.control_data)

    # customer section methods
    def customer_Main(self):
        self.control_data["page"] = "customers"
        self.control_data["customerSearchPanel"] = self.customer_SearchPanel()
        self.control_data["customerActionPanel"] = self.customer_MainActionPanel()

        customersAll = customer.loadAllCustomers(self.database)
        customersAcceptMarketing = {k: v for k, v in customersAll.items() if v["accepts_marketing"] == "true"}
        customerRepeat = {k: v for k, v in customersAll.items() if v["user_id"] != None}

        self.control_data["table_customersAll"] = render_template("control_panel/customer/table_customersAll.html",
                                                                  customers=customersAll)
        self.control_data["table_customersAcceptMarketing"] = render_template(
            "control_panel/customer/table_customersAcceptMarketing.html", customers=customersAcceptMarketing)
        self.control_data["table_customersRepeat"] = render_template(
            "control_panel/customer/table_customersRepeat.html", customers=customerRepeat)

        return render_template("control_panel/customer/Main.html", control_data=self.control_data)

    def customer_CustomerEditor(self, customer_id):
        self.control_data["page"] = "customer_editor"
        self.control_data["customer_id"] = customer_id

        # orderData = loadOrder(customer_id, self.database)
        customerData = loadCustomer(customer_id, self.database)
        orderData = order.loadCustomerOrders(customer_id, self.database)
        if not orderData:
            orderData = {}

        self.control_data["customer_editor_modals"] = render_template(
            "control_panel/customer/modal_customerEditor.html", customer_data=customerData)
        self.control_data["customer_data"] = customerData
        self.control_data["customer_orders"] = orderData

        return render_template("control_panel/customer/CustomerEditor.html", control_data=self.control_data)

    # panels and misc.
    def customer_SearchPanel(self):
        return render_template("control_panel/customer/SearchPanel.html", control_data=self.control_data)

    def customer_MainActionPanel(self):
        return render_template("control_panel/customer/ActionPanel.html", control_data=self.control_data)

    # settings section methods
    def settings_Main(self):
        self.control_data["page"] = "settings"
        return render_template("control_panel/settings/Main.html", control_data=self.control_data)

    def settings_Payment(self):
        self.control_data["page"] = "settings_payment"
        stripe_api_keys = config.getStripeAPIKeys(self.instance_db)
        self.control_data["stripe_api_keys"] = stripe_api_keys

        return render_template("control_panel/settings/Payment.html", control_data=self.control_data)

    def settings_Shipping(self):
        self.control_data["page"] = "settings_shipping"

        shippo_api_keys = config.getShippoAPIKeys(self.instance_db)
        default_shipping_address = config.getDefaultShippingAddress(self.instance_db)

        package_types = config.getPackageTypes(self.instance_db)

        print "Package types: ", package_types

        self.control_data["package_table"] = render_template("control_panel/settings/packageTable.html",
                                                             package_types=package_types)

        self.control_data["shippo_api_keys"] = shippo_api_keys
        self.control_data["default_shipping_address"] = default_shipping_address

        country_list = config.CountryList(self.instance_db)
        rendered_country_list = render_template("control_panel/settings/country_list.html", country_list=country_list,
                                                default_shipping_address=default_shipping_address)

        self.control_data["modals"] = [
            render_template("control_panel/settings/modal_edit_shipping_address.html", address=default_shipping_address,
                            country_list=rendered_country_list),
            render_template("control_panel/settings/modal_edit_package.html")]

        return render_template("control_panel/settings/Shipping.html", control_data=self.control_data)

    def settings_Advanced(self, flag=None):
        self.control_data["page"] = "settings_advanced"

        self.control_data["redis_config"] = config.getRedisSettings(self.instance_db)
        self.control_data["database_config"] = config.getDatabaseSettings(self.instance_db)

        if flag != None:
            self.control_data["error_message"] = ERROR_CODES[flag]
        else:
            self.control_data["error_message"] = None

        self.control_data["modals"] = [render_template("control_panel/settings/modal_confirm_settings.html")]

        return render_template("control_panel/settings/Advanced.html", control_data=self.control_data)

    # store settings section methods
    def store_settings_Main(self):
        self.control_data["page"] = "store_settings"

        return render_template("control_panel/store_settings/Main.html", control_data=self.control_data)

    def store_settings_Pages(self):
        self.control_data["page"] = "store_settings_pages"

        return render_template("control_panel/store_settings/Navigation.html", control_data=self.control_data)

    def store_settings_Footer(self):
        self.control_data["page"] = "store_settings_footer"

        footer_categories = store.getFooterCategories(self.database)

        if footer_categories != {}:
            formattedFooterCategories = {}
            for footer_category, footer_data in footer_categories.iteritems():
                formattedFooterCategories[footer_category] = {}
                for footer_item in footer_data:
                    footer_item = footer_item.split(':')
                    formattedFooterCategories[footer_category][footer_item[0]] = footer_item[1]

            for footerCategory, footerData in formattedFooterCategories.iteritems():
                resource_id = formattedFooterCategories[footerCategory]["resource_id"]
                formattedFooterCategories[footerCategory]["resource"] = resources.loadResourceURI(resource_id,
                                                                                                  self.database)

            self.control_data["footer_categories"] = formattedFooterCategories

        else:
            self.control_data["footer_categories"] = {}

        self.control_data["collections"] = loadCollections(
            self.database)  # this loads all collections for link selection
        self.control_data["content_pages_links"] = ['/page/' + page_id.replace(' ', '%20') for page_id in
                                                    store.getPageIDs(
                                                        self.database)]  # need to write a fn to pull static pages
        print "Content pages:", self.control_data["content_pages_links"]

        return render_template("control_panel/store_settings/Footer.html", control_data=self.control_data)

    def store_settings_Navigation(self):
        self.control_data["page"] = "store_settings_navigation"

        # grab the current navigation categories from the store database in the database
        nav_categories = store.getNavCategories(self.database)

        formattedNavCategories = {}
        for nav_category, nav_data in nav_categories.iteritems():
            formattedNavCategories[nav_category] = {}
            for nav_item in nav_data:
                nav_item = nav_item.split(':')
                formattedNavCategories[nav_category][nav_item[0]] = nav_item[1]

        for navCategory, navData in formattedNavCategories.iteritems():
            resource_id = formattedNavCategories[navCategory]["resource_id"]
            formattedNavCategories[navCategory]["resource"] = resources.loadResourceURI(resource_id, self.database)

        if nav_categories:
            self.control_data["nav_categories"] = formattedNavCategories

        return render_template("control_panel/store_settings/Navigation.html", control_data=self.control_data)

    def store_settings_Pages(self):
        self.control_data["page"] = "store_settings_pages"

        pages = store.getPages(self.database)

        page_table = render_template("control_panel/store_settings/table_pages.html", pages=pages)
        self.control_data["page_table"] = page_table

        page_types = store.getPageTypes(self.database)
        if page_types:
            self.control_data["page_types"] = page_types
        else:
            self.control_data["page_types"] = None

        page_templates = store.getPageTemplates(self.database)
        if page_templates:
            self.control_data["page_templates"] = page_templates
        else:
            self.control_data["page_templates"] = None

        self.control_data["modals"] = render_template("control_panel/store_settings/modal_add_page.html",
                                                      page_types=page_types, page_templates=page_templates)

        return render_template("control_panel/store_settings/Pages.html", control_data=self.control_data)

    def store_settings_PageEditor(self, page_id):
        self.control_data["page"] = "store_settings_page_editor"

        page = store.getPage(page_id, self.database)
        if page:
            self.control_data["page"] = page

        page_types = store.getPageTypes(self.database)
        if page_types:
            self.control_data["page_types"] = page_types

        page_templates = store.getPageTemplates(self.database)
        if page_templates:
            self.control_data["page_templates"] = page_templates

        return render_template("control_panel/store_settings/PageEditor.html", control_data=self.control_data)

    def store_settings_Analytics(self):
        self.control_data["page"] = "store_settings_analytics"
        self.control_data["modals"] = []

        self.control_data["analytics_script"] = config.getGoogleAnalyticsScript(self.instance_db)

        return render_template("control_panel/store_settings/Analytics.html", control_data=self.control_data)

    def store_settings_FileManager(self):
        self.control_data["page"] = "store_settings_file_manager"

        resource_dict = resources.loadResourcesByType("uploaded_file", self.database)

        resource_table = render_template("control_panel/store_settings/table_files.html", resources=resource_dict)

        self.control_data["resource_table"] = resource_table
        self.control_data["fileActionPanel"] = self.store_settings_FileActionPanel()
        self.control_data["modals"] = render_template("control_panel/store_settings/modal_upload_file.html")

        return render_template("control_panel/store_settings/FileManager.html", control_data=self.control_data)

    def store_settings_ThemeManager(self):
        self.control_data["page"] = "store_settings_theme_manager"

        pages = store.getPages(self.database)
        if pages:
            self.control_data["pages"] = pages

        page_types = store.getPageTypes(self.database)
        if page_types:
            self.control_data["page_types"] = page_types

        page_templates = store.getPageTemplates(self.database)
        if page_templates:
            self.control_data["page_templates"] = page_templates

        section_templates = store.getSectionTemplates(self.database)
        if section_templates:
            self.control_data["section_templates"] = section_templates

        self.control_data["rendered_sections"] = {}
        for section_id, section_data in section_templates.iteritems():
            current_template = render_template(section_data["template_file"])
            self.control_data["rendered_sections"][section_id] = current_template
            print self.control_data["rendered_sections"][section_id]

        resource_dict = resources.loadResourcesByType("uploaded_file", self.database)

        if resource_dict:
            self.control_data["resources"] = resource_dict

        self.control_data["modals"] = [render_template("control_panel/store_settings/modal_edit_section.html"),
                                       render_template("control_panel/store_settings/modal_add_section.html"),
                                       render_template("control_panel/store_settings/modal_delete_section.html")]

        return render_template("control_panel/store_settings/ThemeManager.html", control_data=self.control_data)

    def store_settings_FileActionPanel(self):
        return render_template("control_panel/store_settings/FileActionPanel.html", control_data=self.control_data)

    # plugins section methods

    def plugins_Main(self):
        allPlugins = plugins.loadAllPlugins(self.database)
        python_utils = {}

        lyra_utility = imp.load_source('lyra_utility', 'plugins/lyra_utility.py')

        for plugin_id, plugin in allPlugins.iteritems():
            if plugin["plugin_type"] == "python_utility":
                plugin_name = plugin["plugin_name"]

                # loads the plugin module from stored URI
                current_pluggin_module = imp.load_source(plugin_name, plugin["uri"])

                # looks for a class with the current plugin's name (stored ID)
                if hasattr(current_pluggin_module, plugin_name):
                    plugin_class = getattr(current_pluggin_module, plugin_name)
                    python_utils[plugin_name] = plugin_class  # handle to class, not an instance

                # instance will be initialized upon run

        self.control_data["table_pythonUtil"] = render_template("control_panel/plugins/table_pythonUtil.html",
                                                                pythonUtil=allPlugins)
        return render_template("control_panel/plugins/Main.html", control_data=self.control_data)

    # loads a python plugin
    def plugins_PyUtil(self, data):
        plugin_id = data
        # load super class for python utility
        lyra_utility = imp.load_source('lyra_utility', 'plugins/lyra_utility.py')

        # load python utility record from db
        plugin_data = plugins.loadPluginByID(plugin_id, self.database)

        # make sure it's a pyutil plugin
        if plugin_data["plugin_type"] == "python_utility":
            plugin_name = plugin_data["plugin_name"]

            # loads the plugin module from stored URI
            current_pluggin_module = imp.load_source(plugin_name, plugin_data["uri"])

            # looks for a class with the current plugin's name (stored ID)
            if hasattr(current_pluggin_module, plugin_name):
                plugin_class = getattr(current_pluggin_module, plugin_name)
                plugin = plugin_class  # handle to class, not an instance

            # instance will be initialized upon run

        inputs = {"test": "test"}

        ali = plugin(inputs)

        params = {"message": "hello world!"}

        ali.run_function("say_hello", params)

        plugin_log = ali.output_log

        self.control_data["plugin_log"] = plugin_log
        self.control_data["plugin_data"] = plugin_data

        return render_template("control_panel/plugins/PythonUtility.html", control_data=self.control_data)

    # dashboard section methods

    def dashboard_Main(self):
        self.control_data["page"] = "dashboard"
        dashboard_tiles = dashboard.loadAllDashboardTiles(self.database)

        rendered_tiles = {}
        rendered_plots = {}

        for tile_id, tile_data in dashboard_tiles.iteritems():
            if tile_data["tile_type"] == "data-feed":

                tile_data["requirements"] = parseDataFeed_requirements(tile_data)

                if tile_data["requirements"]["tile_page"] != "main":
                    continue

                tile_data["helper_script"] = load_FeedHelperScript(tile_data["requirements"]["helper_script"])

                helper_instance = tile_data["helper_script"](tile_data["requirements"]["query_file"],
                                                             tile_data["requirements"]["template_file"],
                                                             tile_data["requirements"]["data_sources"])

                data_sources = set(helper_instance.data_sources.split(','))

                source_handles = {}

                for source_id in data_sources:
                    if source_id == "order":
                        source_handles["order"] = order
                    elif source_id == "product":
                        source_handles["product"] = product
                    elif source_id == "config":
                        source_handles["config"] = config
                    elif source_id == "store":
                        source_handles["store"] = store
                    elif source_id == "message":
                        source_handles["message"] = message

                helper_instance.set_database(
                    self.database)  # point the helper instance at the data source for query file
                helper_instance.load_data_sources(source_handles)  # load local db functions, if necessary

                helper_instance.run_script()

                template_data = helper_instance.template_data

                tile_template = render_template(
                    "control_panel/dashboard/tile_templates/" + helper_instance.template_file,
                    template_data=template_data)

                rendered_tiles[tile_id] = tile_template



            # bokeh tile type dashboard element
            elif tile_data["tile_type"] == "data-plot":

                tile_data["requirements"] = parseDataFeed_requirements(tile_data)

                if tile_data["requirements"]["tile_page"] != "main":
                    continue

                template_file_uri = tile_data["requirements"]["template_file"]

                tile_template = render_template("control_panel/dashboard/tile_templates/" + template_file_uri,
                                                tile_data=tile_data)

                rendered_plots[tile_id] = tile_template

        self.control_data["rendered_tiles"] = rendered_tiles
        self.control_data["rendered_plots"] = rendered_plots

        return render_template("control_panel/dashboard/Main.html", control_data=self.control_data)

    def dashboard_LiveChat(self):
        self.control_data["page"] = "dashboard_live_chat"
        dashboard_tiles = dashboard.loadAllDashboardTiles(self.database)

        rendered_tiles = {}
        rendered_plots = {}

        for tile_id, tile_data in dashboard_tiles.iteritems():
            if tile_data["tile_type"] == "data-feed":

                tile_data["requirements"] = parseDataFeed_requirements(tile_data)

                if tile_data["requirements"]["tile_page"] != "live_chat":
                    continue

                tile_data["helper_script"] = load_FeedHelperScript(tile_data["requirements"]["helper_script"])

                helper_instance = tile_data["helper_script"](tile_data["requirements"]["query_file"],
                                                             tile_data["requirements"]["template_file"],
                                                             tile_data["requirements"]["data_sources"])

                data_sources = set(helper_instance.data_sources.split(','))

                source_handles = {}

                for source_id in data_sources:
                    if source_id == "order":
                        source_handles["order"] = order
                    elif source_id == "product":
                        source_handles["product"] = product
                    elif source_id == "config":
                        source_handles["config"] = config
                    elif source_id == "store":
                        source_handles["store"] = store
                    elif source_id == "message":
                        source_handles["message"] = message

                helper_instance.set_database(
                    self.database)  # point the helper instance at the data source for query file
                helper_instance.load_data_sources(source_handles)  # load local db functions, if necessary

                helper_instance.run_script()

                template_data = helper_instance.template_data

                tile_template = render_template(
                    "control_panel/dashboard/tile_templates/" + helper_instance.template_file,
                    template_data=template_data)

                rendered_tiles[tile_id] = tile_template



            # bokeh tile type dashboard element
            elif tile_data["tile_type"] == "data-plot":

                tile_data["requirements"] = parseDataFeed_requirements(tile_data)

                if tile_data["requirements"]["tile_page"] != "live_chat":
                    continue

                template_file_uri = tile_data["requirements"]["template_file"]

                tile_template = render_template("control_panel/dashboard/tile_templates/" + template_file_uri,
                                                tile_data=tile_data)

                rendered_plots[tile_id] = tile_template

        self.control_data["rendered_tiles"] = rendered_tiles
        self.control_data["rendered_plots"] = rendered_plots

        return render_template("control_panel/dashboard/LiveChat.html", control_data=self.control_data)
